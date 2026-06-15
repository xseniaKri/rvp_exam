"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("login", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("middle_name", sa.String(length=100), nullable=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
    )

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "book_genres",
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("book_id", "genre_id"),
    )

    op.create_table(
        "covers",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("md5_hash", sa.String(length=32), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "user_id", name="uq_review_book_user"),
    )

    # Seed roles
    op.execute(
        "INSERT INTO roles (name, description) VALUES "
        "('Администратор', 'Суперпользователь, имеет полный доступ к системе, в том числе к созданию и удалению книг'), "
        "('Модератор', 'Может редактировать данные книг и производить модерацию рецензий'), "
        "('Пользователь', 'Может оставлять рецензии')"
    )

    op.execute(
        "INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id) VALUES "
        "('admin',     'scrypt:32768:8:1$ABIvIKfpmWKnnkPv$b430aad88814ff376e89c82d2976f291c2d8284cd514795fd8a6a27e61fba2e61bcd57594840a692c96cca1f769c6564a96d3d9bc51ff3fd34fd019c16778504', "
        " 'Иванов',  'Иван',    'Иванович',  (SELECT id FROM roles WHERE name = 'Администратор')), "
        "('moderator', 'scrypt:32768:8:1$WIGEba5pbmA9E0YG$96767f8583a5098dd4237d654159ea359636f0b3d6998024d843dbbcf54024b4e1da34693d60a3f21772739fecb81381328907c6107830dfcb8e6f1e3e82e405', "
        " 'Петрова', 'Мария',   'Сергеевна', (SELECT id FROM roles WHERE name = 'Модератор')), "
        "('user',      'scrypt:32768:8:1$DJj5BTHU6qOxgw9I$e90173e4b31488852ca9812aeec7b72e4f8766a236d6b9dec2a5babf3eeec5afeeb04a58957f32965f111c9ba4471359ad9e702ff560938a0f9ab1f4a48153b8', "
        " 'Сидоров', 'Алексей', NULL,        (SELECT id FROM roles WHERE name = 'Пользователь'))"
    )

    # Seed genres
    op.execute(
        "INSERT INTO genres (name) VALUES "
        "('Роман'), ('Фантастика'), ('Детектив'), ('Исторический'), ('Поэзия')"
    )

    # Seed books (15 классических произведений)
    op.execute(sa.text("""
        INSERT INTO books (title, description, year, publisher, author, pages) VALUES
        ('Война и мир',
         'Роман-эпопея о судьбах нескольких дворянских семей в годы Отечественной войны 1812 года.',
         1869, 'Отечественные записки', 'Лев Толстой', 1274),
        ('Преступление и наказание',
         'История студента Раскольникова, совершившего убийство и мучимого угрызениями совести.',
         1866, 'Русский вестник', 'Фёдор Достоевский', 672),
        ('Мастер и Маргарита',
         'Сатирический роман о визите Воланда в советскую Москву и истории Мастера и его возлюбленной.',
         1967, 'Москва', 'Михаил Булгаков', 480),
        ('Евгений Онегин',
         'Роман в стихах о судьбе молодого петербургского аристократа и его несостоявшейся любви.',
         1833, 'Смирдин', 'Александр Пушкин', 224),
        ('Отцы и дети',
         'Роман о конфликте поколений, нигилизме и любви на фоне пореформенной России.',
         1862, 'Русский вестник', 'Иван Тургенев', 296),
        ('Мёртвые души',
         'Поэма о похождениях предприимчивого Чичикова, скупающего крепостных крестьян.',
         1842, 'Трутовский', 'Николай Гоголь', 352),
        ('Обломов',
         'История русского дворянина, погружённого в апатию и бездействие на диване.',
         1859, 'Отечественные записки', 'Иван Гончаров', 496),
        ('Герой нашего времени',
         'Психологический роман об офицере Печорине и его губительном влиянии на окружающих.',
         1840, 'Ильяшенко', 'Михаил Лермонтов', 208),
        ('Анна Каренина',
         'Роман о трагической любви замужней светской дамы и блестящего офицера Вронского.',
         1878, 'Русский вестник', 'Лев Толстой', 864),
        ('Идиот',
         'История о добром и наивном князе Мышкине, столкнувшемся с жестокостью петербургского общества.',
         1869, 'Русский вестник', 'Фёдор Достоевский', 640),
        ('Братья Карамазовы',
         'Философский роман о трёх братьях Карамазовых и загадочном убийстве их отца.',
         1880, 'Русский вестник', 'Фёдор Достоевский', 940),
        ('Вишнёвый сад',
         'Пьеса о гибели старинного дворянского поместья и неумолимом ходе времени.',
         1904, 'Знание', 'Антон Чехов', 96),
        ('Капитанская дочка',
         'Исторический роман о пугачёвском восстании глазами молодого офицера Петра Гринёва.',
         1836, 'Современник', 'Александр Пушкин', 192),
        ('Ревизор',
         'Комедия о том, как чиновники провинциального города приняли мелкого чиновника за ревизора.',
         1836, 'Александрийский театр', 'Николай Гоголь', 112),
        ('Доктор Живаго',
         'Роман о судьбе врача и поэта Юрия Живаго в годы революции и Гражданской войны.',
         1957, 'Фельтринелли', 'Борис Пастернак', 576)
    """))

    # Seed covers (filename = порядковый номер книги по вставке + .jpg)
    op.execute(sa.text("""
        INSERT INTO covers (filename, mime_type, md5_hash, book_id)
        SELECT '1.jpg',  'image/jpeg', '84673a644221e97989830933ed0d76e1', id FROM books WHERE title = 'Война и мир'           UNION ALL
        SELECT '2.jpg',  'image/jpeg', '7bb470e96469289ffcca18a59c395b63', id FROM books WHERE title = 'Преступление и наказание' UNION ALL
        SELECT '3.jpg',  'image/jpeg', '009e517b0a4eb2897ee9a007bc5b36fb', id FROM books WHERE title = 'Мастер и Маргарита'     UNION ALL
        SELECT '4.jpg',  'image/jpeg', 'd51a8aa686f4782bfd3c849e88191cc7', id FROM books WHERE title = 'Евгений Онегин'          UNION ALL
        SELECT '5.jpg',  'image/jpeg', 'e611a5c31b68f07d8de9433eee2b7c08', id FROM books WHERE title = 'Отцы и дети'             UNION ALL
        SELECT '6.jpg',  'image/jpeg', '35e469bfdbdbe03c7c5ad3285d52a8e1', id FROM books WHERE title = 'Мёртвые души'            UNION ALL
        SELECT '7.jpg',  'image/jpeg', 'a17bfc78d3d336e6cd5b65627d7a357f', id FROM books WHERE title = 'Обломов'                 UNION ALL
        SELECT '8.jpg',  'image/jpeg', 'd9da5826306754157d1d6641234904c3', id FROM books WHERE title = 'Герой нашего времени'    UNION ALL
        SELECT '9.jpg',  'image/jpeg', 'fb1874d1bd8d589d788c115826a889a9', id FROM books WHERE title = 'Анна Каренина'           UNION ALL
        SELECT '10.jpg', 'image/jpeg', '944309314ed8dcce2d7b1b21660314f0', id FROM books WHERE title = 'Идиот'                   UNION ALL
        SELECT '11.jpg', 'image/jpeg', '352db07093a64508f8a529dfece7820e', id FROM books WHERE title = 'Братья Карамазовы'       UNION ALL
        SELECT '12.jpg', 'image/jpeg', '7e038bdba9d18c4758fdc784d3863117', id FROM books WHERE title = 'Вишнёвый сад'            UNION ALL
        SELECT '13.jpg', 'image/jpeg', '638648e8daa0ddfe19178efb42f63eda', id FROM books WHERE title = 'Капитанская дочка'       UNION ALL
        SELECT '14.jpg', 'image/jpeg', '54fe096b3ccc85c9204582d0d50966c1', id FROM books WHERE title = 'Ревизор'                 UNION ALL
        SELECT '15.jpg', 'image/jpeg', 'e889e8f980523a4241e636d9a1bd1be2', id FROM books WHERE title = 'Доктор Живаго'
    """))

    # Seed book_genres
    op.execute(sa.text("""
        INSERT INTO book_genres (book_id, genre_id)
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Война и мир'             AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Война и мир'             AND g.name = 'Исторический'     UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Преступление и наказание' AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Преступление и наказание' AND g.name = 'Детектив'         UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Мастер и Маргарита'      AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Мастер и Маргарита'      AND g.name = 'Фантастика'       UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Евгений Онегин'          AND g.name = 'Поэзия'           UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Отцы и дети'             AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Мёртвые души'            AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Обломов'                 AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Герой нашего времени'    AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Анна Каренина'           AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Идиот'                   AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Братья Карамазовы'       AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Вишнёвый сад'            AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Капитанская дочка'       AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Капитанская дочка'       AND g.name = 'Исторический'     UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Ревизор'                 AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Доктор Живаго'           AND g.name = 'Роман'            UNION ALL
        SELECT b.id, g.id FROM books b, genres g WHERE b.title = 'Доктор Живаго'           AND g.name = 'Исторический'
    """))


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("covers")
    op.drop_table("book_genres")
    op.drop_table("books")
    op.drop_table("genres")
    op.drop_table("users")
    op.drop_table("roles")
