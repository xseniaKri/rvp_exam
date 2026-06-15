import hashlib
import os
from functools import wraps

import bleach
import markdown2
from flask import current_app, flash, redirect, url_for
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func, select
from werkzeug.utils import secure_filename

_ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "del", "em",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img",
    "li", "ol", "p", "pre", "s", "strong", "table", "tbody",
    "td", "th", "thead", "tr", "ul",
}
_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "abbr": ["title"],
    "img": ["src", "alt", "title"],
    "td": ["align"],
    "th": ["align"],
}


def sanitize_description(text: str) -> str:
    return bleach.clean(text, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)


def render_markdown(text: str) -> Markup:
    html = markdown2.markdown(
        text or "",
        extras=["fenced-code-blocks", "tables", "strike", "break-on-newline"],
    )
    return Markup(html)


def _upload_folder() -> str:
    return os.path.join(current_app.root_path, current_app.config["UPLOAD_FOLDER"])


def save_cover(file, book_id: int) -> "tuple[Cover, bytes | None]":
    from app.models import Cover

    data = file.read()
    md5 = hashlib.md5(data).hexdigest()
    mime_type = file.mimetype

    existing = current_app.extensions["sqlalchemy"].session.execute(
        select(Cover).where(Cover.md5_hash == md5)
    ).scalar_one_or_none()

    if existing:
        return Cover(filename=existing.filename, mime_type=mime_type, md5_hash=md5, book_id=book_id), None

    # New unique file — create row first to get the auto-increment ID
    cover = Cover(filename="", mime_type=mime_type, md5_hash=md5, book_id=book_id)
    db_session = current_app.extensions["sqlalchemy"].session
    db_session.add(cover)
    db_session.flush()

    _, ext = os.path.splitext(secure_filename(file.filename))
    cover.filename = f"{cover.id}{ext.lower()}"

    return cover, data


def write_cover_file(cover, data: bytes) -> None:
    dest = os.path.join(_upload_folder(), cover.filename)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(data)


def delete_cover_file(cover) -> None:
    from app.models import Cover

    db_session = current_app.extensions["sqlalchemy"].session
    other_refs = db_session.execute(
        select(func.count())
        .select_from(Cover)
        .where(Cover.filename == cover.filename)
        .where(Cover.book_id != cover.book_id)
    ).scalar_one()

    if other_refs == 0:
        path = os.path.join(_upload_folder(), cover.filename)
        if os.path.exists(path):
            os.remove(path)


def role_required(*role_names):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(
                    "Для выполнения данного действия необходимо пройти процедуру аутентификации",
                    "warning",
                )
                return redirect(url_for("auth.login"))
            if current_user.role.name not in role_names:
                flash("У вас недостаточно прав для выполнения данного действия", "danger")
                return redirect(url_for("books.index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator
