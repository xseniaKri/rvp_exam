import logging
import os

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request, url_for,
)

logger = logging.getLogger(__name__)
from flask_login import current_user
from sqlalchemy import func, select

from app import db
from app.models import Book, Collection, Genre, Review
from app.utils import delete_cover_file, role_required, sanitize_description, save_cover, write_cover_file

books_bp = Blueprint("books", __name__)

PER_PAGE = 10


def _books_with_stats_query():
    return (
        select(
            Book,
            func.count(Review.id).label("review_count"),
            func.avg(Review.rating).label("avg_rating"),
        )
        .outerjoin(Review, Review.book_id == Book.id)
        .group_by(Book.id)
        .order_by(Book.year.desc(), Book.id.desc())
    )


@books_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)

    total = db.session.execute(
        select(func.count()).select_from(Book)
    ).scalar_one()

    rows = db.session.execute(
        _books_with_stats_query().offset((page - 1) * PER_PAGE).limit(PER_PAGE)
    ).all()

    books = [
        {"book": row.Book, "review_count": row.review_count, "avg_rating": row.avg_rating}
        for row in rows
    ]

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "books/index.html",
        books=books,
        page=page,
        total_pages=total_pages,
    )


@books_bp.route("/books/<int:book_id>")
def detail(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    reviews = db.session.execute(
        select(Review)
        .where(Review.book_id == book_id)
        .order_by(Review.created_at.desc())
    ).scalars().all()

    user_review = None
    user_collections = []
    if current_user.is_authenticated:
        user_review = db.session.execute(
            select(Review).where(
                Review.book_id == book_id,
                Review.user_id == current_user.id,
            )
        ).scalar_one_or_none()
        if current_user.is_user:
            user_collections = db.session.execute(
                select(Collection)
                .where(Collection.user_id == current_user.id)
                .order_by(Collection.name)
            ).scalars().all()

    return render_template(
        "books/detail.html",
        book=book,
        reviews=reviews,
        user_review=user_review,
        user_collections=user_collections,
    )


@books_bp.route("/books/add", methods=["GET", "POST"])
@role_required("Администратор")
def add():
    genres = db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()

    if request.method == "POST":
        values = request.form
        genre_ids = request.form.getlist("genre_ids", type=int)
        cover_file = request.files.get("cover")

        error = _validate_book_form(values, genre_ids, require_cover=True, cover_file=cover_file)
        if error:
            flash(error, "danger")
            return render_template(
                "books/add.html", genres=genres, values=values, selected_genre_ids=genre_ids
            )

        try:
            book = Book(
                title=values["title"].strip(),
                description=sanitize_description(values["description"].strip()),
                year=int(values["year"]),
                publisher=values["publisher"].strip(),
                author=values["author"].strip(),
                pages=int(values["pages"]),
            )
            selected_genres = db.session.execute(
                db.select(Genre).where(Genre.id.in_(genre_ids))
            ).scalars().all()
            book.genres = selected_genres

            db.session.add(book)
            db.session.flush()

            cover, cover_data = save_cover(cover_file, book.id)
            cover_filename = cover.filename
            book.cover = cover

            db.session.commit()
        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template(
                "books/add.html", genres=genres, values=values, selected_genre_ids=genre_ids
            )

        if cover_data is not None:
            try:
                write_cover_file(cover_filename, cover_data)
            except Exception:
                logger.exception("Не удалось сохранить файл обложки: %s", cover_filename)

        flash(f"Книга «{book.title}» успешно добавлена", "success")
        return redirect(url_for("books.detail", book_id=book.id))

    return render_template(
        "books/add.html", genres=genres, values={}, selected_genre_ids=[]
    )


@books_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@role_required("Администратор", "Модератор")
def edit(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    genres = db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()

    if request.method == "POST":
        values = request.form
        genre_ids = request.form.getlist("genre_ids", type=int)

        error = _validate_book_form(values, genre_ids, require_cover=False)
        if error:
            flash(error, "danger")
            return render_template(
                "books/edit.html",
                book=book, genres=genres, values=values, selected_genre_ids=genre_ids,
            )

        try:
            book.title = values["title"].strip()
            book.description = sanitize_description(values["description"].strip())
            book.year = int(values["year"])
            book.publisher = values["publisher"].strip()
            book.author = values["author"].strip()
            book.pages = int(values["pages"])
            book.genres = db.session.execute(
                db.select(Genre).where(Genre.id.in_(genre_ids))
            ).scalars().all()

            db.session.commit()
            flash(f"Книга «{book.title}» успешно обновлена", "success")
            return redirect(url_for("books.detail", book_id=book.id))

        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template(
                "books/edit.html",
                book=book, genres=genres, values=values, selected_genre_ids=genre_ids,
            )

    values = {
        "title": book.title,
        "description": book.description,
        "year": book.year,
        "publisher": book.publisher,
        "author": book.author,
        "pages": book.pages,
    }
    selected_genre_ids = [g.id for g in book.genres]
    return render_template(
        "books/edit.html",
        book=book, genres=genres, values=values, selected_genre_ids=selected_genre_ids,
    )


@books_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@role_required("Администратор")
def delete(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    title = book.title

    if book.cover:
        delete_cover_file(book.cover)

    db.session.delete(book)
    db.session.commit()

    flash(f"Книга «{title}» успешно удалена", "success")
    return redirect(url_for("books.index"))


def _validate_book_form(values, genre_ids, *, require_cover, cover_file=None):
    required_fields = {
        "title": "Название",
        "description": "Краткое описание",
        "year": "Год",
        "publisher": "Издательство",
        "author": "Автор",
        "pages": "Объём",
    }
    for field, label in required_fields.items():
        if not values.get(field, "").strip():
            return "При сохранении данных возникла ошибка. Проверьте корректность введённых данных."

    if not genre_ids:
        return "При сохранении данных возникла ошибка. Проверьте корректность введённых данных."

    try:
        year = int(values["year"])
        if not (1000 <= year <= 2100):
            raise ValueError
    except (ValueError, KeyError):
        return "При сохранении данных возникла ошибка. Проверьте корректность введённых данных."

    try:
        pages = int(values["pages"])
        if pages < 1:
            raise ValueError
    except (ValueError, KeyError):
        return "При сохранении данных возникла ошибка. Проверьте корректность введённых данных."

    if require_cover and (not cover_file or cover_file.filename == ""):
        return "При сохранении данных возникла ошибка. Проверьте корректность введённых данных."

    return None
