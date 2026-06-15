from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        user = db.session.execute(
            db.select(User).where(User.login == login)
        ).scalar_one_or_none()
        remember = bool(request.form.get("remember"))
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return redirect(request.args.get("next") or url_for("books.index"))
        flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("books.index"))
