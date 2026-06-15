from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.utils import render_markdown
    app.jinja_env.filters["markdown"] = render_markdown

    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.reviews import reviews_bp
    from app.routes.collections import collections_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(collections_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    from app import db
    return db.session.get(User, int(user_id))
