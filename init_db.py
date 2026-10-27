"""Создаёт таблицы БД и выполняет простые миграции (добавление новых колонок)."""
from sqlalchemy import inspect, text

from app.database import engine, Base
from app.models import User, Worksheet, Task, Lesson, TodoItem

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
    conn.commit()

print("✅ Таблицы готовы в", engine.url)
