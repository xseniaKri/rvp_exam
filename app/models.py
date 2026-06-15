from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, ForeignKey, Table, TIMESTAMP, UniqueConstraint,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


collection_books = Table(
    "collection_books",
    Base.metadata,
    Column("collection_id", Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
)

book_genres = Table(
    "book_genres",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")
    reviews = relationship("Review", back_populates="user")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def is_admin(self):
        return self.role.name == "Администратор"

    @property
    def is_moderator(self):
        return self.role.name in ("Администратор", "Модератор")

    @property
    def is_user(self):
        return self.role.name == "Пользователь"


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    books = relationship("Book", secondary=book_genres, back_populates="genres")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    year = Column(SmallInteger, nullable=False)
    publisher = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    pages = Column(Integer, nullable=False)

    genres = relationship("Genre", secondary=book_genres, back_populates="books")
    cover = relationship("Cover", back_populates="book", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    collections = relationship("Collection", secondary=collection_books, back_populates="books")


class Cover(Base):
    __tablename__ = "covers"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    md5_hash = Column(String(32), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    book = relationship("Book", back_populates="cover")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("book_id", "user_id", name="uq_review_book_user"),
    )

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="collections")
    books = relationship("Book", secondary=collection_books, back_populates="collections")
