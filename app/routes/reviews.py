from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from app import db
from app.models import Book, Review
from app.utils import sanitize_description

reviews_bp = Blueprint("reviews", __name__)

RATING_LABELS = {
    5: "Отлично",
    4: "Хорошо",
    3: "Удовлетворительно",
    2: "Неудовлетворительно",
    1: "Плохо",
    0: "Ужасно",
}


@reviews_bp.route("/books/<int:book_id>/reviews/new", methods=["GET", "POST"])
@login_required
def new(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        from flask import abort
        abort(404)

    existing = db.session.execute(
        select(Review).where(
            Review.book_id == book_id,
            Review.user_id == current_user.id,
        )
    ).scalar_one_or_none()
    if existing:
        flash("Вы уже оставляли рецензию на эту книгу", "warning")
        return redirect(url_for("books.detail", book_id=book_id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        text = request.form.get("text", "").strip()

        if rating is None or rating not in RATING_LABELS or not text:
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template(
                "reviews/new.html",
                book=book,
                values=request.form,
                rating_labels=RATING_LABELS,
            )

        try:
            review = Review(
                book_id=book_id,
                user_id=current_user.id,
                rating=rating,
                text=sanitize_description(text),
            )
            db.session.add(review)
            db.session.commit()
            flash("Рецензия успешно добавлена", "success")
            return redirect(url_for("books.detail", book_id=book_id))

        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. Проверьте корректность введённых данных.",
                "danger",
            )
            return render_template(
                "reviews/new.html",
                book=book,
                values=request.form,
                rating_labels=RATING_LABELS,
            )

    return render_template(
        "reviews/new.html",
        book=book,
        values={},
        rating_labels=RATING_LABELS,
    )
