"""Создаёт таблицы БД и выполняет простые миграции (добавление новых колонок)."""
from sqlalchemy import inspect, text

from app.database import engine, Base
from app.models import User, Worksheet, Task, Lesson, TodoItem, Assignment

print("Создаём таблицы...")
Base.metadata.create_all(bind=engine)

# Простая миграция: добавляем недостающие колонки в существующие таблицы
with engine.connect() as conn:
    inspector = inspect(engine)
    for table in Base.metadata.tables.values():
        if not inspector.has_table(table.name):
            continue
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name not in existing:
                col_type = column.type.compile(engine.dialect)
                sql = f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {col_type}'
                print(f"Миграция: {sql}")
                conn.execute(text(sql))

        # Миграция: поле "Тема" дела заменено на "Тип" (todo_type)
        if inspector.has_table("todo_items"):
            todo_cols = {c["name"] for c in inspector.get_columns("todo_items")}
            if "topic" in todo_cols and "todo_type" in todo_cols:
                print("Миграция: переношу значения topic -> todo_type ...")
                rows = conn.execute(
                    text(
                        "SELECT id, topic FROM todo_items "
                        "WHERE (todo_type IS NULL OR todo_type = '') AND topic IS NOT NULL"
                    )
                ).fetchall()
                valid_types = {
                    "встреча", "написать работу", "проверить работу",
                    "ответить на письмо", "другое",
                }
                for row_id, topic_val in rows:
                    v = (topic_val or "").strip().lower()
                    if v in valid_types:
                        conn.execute(
                            text("UPDATE todo_items SET todo_type = :t WHERE id = :i"),
                            {"t": v, "i": row_id},
                        )
    conn.commit()

print("✅ Таблицы готовы в", engine.url)
