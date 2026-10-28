"""Автоматические миграции SQLite при старте приложения.

Добавляет недостающие колонки и таблицы, чтобы сервер не падал с ошибкой
"no such column" после обновления кода без пересоздания базы данных.
"""
from sqlalchemy import inspect, text


def run_migrations(engine):
    """Добавляет в существующие таблицы колонки, которых в них нет."""
    inspector = inspect(engine)
    statements = []
    for table in Base_tables():
        if not inspector.has_table(table.name):
            continue  # create_all создаст её целиком
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in existing:
                col_type = column.type.compile(engine.dialect)
                statements.append(
                    f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {col_type}'
                )
    if not statements:
        return
    with engine.connect() as conn:
        for sql in statements:
            print(f"Миграция БД: {sql}")
            conn.execute(text(sql))
        # Заполняем NULL у старых строк в обязательных полях (иначе
        # pydantic-схема ответа падает на валидации created_at=None)
        from datetime import datetime

        now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        fixes = [
            "UPDATE lessons SET created_at = COALESCE(created_at, '{}')".format(now),
            "UPDATE todos SET created_at = COALESCE(created_at, '{}')".format(now),
            "UPDATE assignments SET created_at = COALESCE(created_at, '{}')".format(now),
            "UPDATE worksheets SET created_at = COALESCE(created_at, '{}')".format(now),
        ]
        for sql_fix in fixes:
            try:
                conn.execute(text(sql_fix))
            except Exception:
                pass  # таблицы может ещё не быть — не критично
        conn.commit()


def Base_tables():
    from app.database import Base

    return Base.metadata.tables.values()
