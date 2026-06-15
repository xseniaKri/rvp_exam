from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from app import db
from app.models import Book, Collection, collection_books
from app.utils import role_required

collections_bp = Blueprint("collections", __name__)


def _own_collection_or_404(collection_id: int) -> Collection:
    col = db.session.get(Collection, collection_id)
    if col is None or col.user_id != current_user.id:
        abort(404)
    return col


@collections_bp.route("/collections")
@role_required("Пользователь")
def index():
    rows = db.session.execute(
        select(
            Collection,
            func.count(collection_books.c.book_id).label("book_count"),
        )
        .outerjoin(collection_books, collection_books.c.collection_id == Collection.id)
        .where(Collection.user_id == current_user.id)
        .group_by(Collection.id)
        .order_by(Collection.name)
    ).all()

    collections = [
        {"collection": row.Collection, "book_count": row.book_count}
        for row in rows
    ]
    return render_template("collections/index.html", collections=collections)


@collections_bp.route("/collections", methods=["POST"])
@role_required("Пользователь")
def create():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Название подборки не может быть пустым", "danger")
        return redirect(url_for("collections.index"))

    col = Collection(name=name, user_id=current_user.id)
    db.session.add(col)
    db.session.commit()
    flash(f"Подборка «{col.name}» успешно создана", "success")
    return redirect(url_for("collections.index"))


@collections_bp.route("/collections/<int:collection_id>")
@role_required("Пользователь")
def detail(collection_id):
    col = _own_collection_or_404(collection_id)
    return render_template("collections/detail.html", collection=col)


@collections_bp.route("/books/<int:book_id>/add-to-collection", methods=["POST"])
@role_required("Пользователь")
def add_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        abort(404)

    collection_id = request.form.get("collection_id", type=int)
    col = _own_collection_or_404(collection_id)

    if book not in col.books:
        col.books.append(book)
        db.session.commit()
        flash(f"Книга «{book.title}» добавлена в подборку «{col.name}»", "success")
    else:
        flash(f"Книга «{book.title}» уже есть в подборке «{col.name}»", "info")

    return redirect(url_for("books.detail", book_id=book_id))
