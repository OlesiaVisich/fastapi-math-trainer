"""Создаёт таблицы БД и выполняет простые миграции (добавление новых колонок)."""
from sqlalchemy import inspect, text

from app.database import engine, Base
from app.models import (
    User, Worksheet, Task, Lesson, TodoItem, Assignment, AssignmentGroup,
)

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

# Наполнение тестовыми данными, если таблицы пустые (для проверки работы сайта)
from app.database import SessionLocal
from sqlalchemy import inspect as _inspect

db = SessionLocal()
try:
    insp = _inspect(engine)

    def _cols(table):
        return {c["name"] for c in insp.get_columns(table)} if insp.has_table(table) else set()

    if insp.has_table("assignments") and db.query(Assignment).count() == 0:
        print("Добавляю тестовые задания...")
        g1 = AssignmentGroup(name="Линейные уравнения")
        db.add(g1)
        db.flush()
        samples = [
            ("$$2x + 5 = 13$$", "9А", "Линейные уравнения", "простая", g1.id),
            ("$$3x - 7 = 2x + 4$$", "9В", "Линейные уравнения", "простая", g1.id),
            ("$$5(x-2) = 3x + 6$$", "9А", "Линейные уравнения", "средняя", g1.id),
            ("$$\\frac{x}{2} + \\frac{x}{3} = 10$$", "10", "Дробые уравнения", "средняя", None),
            ("$$x^2 - 5x + 6 = 0$$", "9Б", "Квадратные уравнения", "высокая", None),
            ("$$x^2 + 4x - 21 = 0$$", "11", "Квадратные уравнения", "высокая", None),
        ]
        for latex, cls, topic, diff, gid in samples:
            db.add(Assignment(school_class=cls, topic=topic,
                              difficulty=diff, latex_code=latex, group_id=gid))
        db.commit()

    if insp.has_table("lessons") and db.query(Lesson).count() == 0:
        print("Добавляю тестовые уроки...")
        db.add_all([
            Lesson(topic="Квадратные уравнения", school_class="8А",
                   description="Теория и решение простейших квадратных уравнений.",
                   homework="§14, №235–240"),
            Lesson(topic="Линейные уравнения", school_class="9В",
                   description="Повторение и отработка навыков решения.",
                   homework="№112, 115"),
        ])
        db.commit()

    if insp.has_table("todo_items") and db.query(TodoItem).count() == 0:
        print("Добавляю тестовые дела...")
        from datetime import date, timedelta
        todo_cols = _cols("todo_items")
        base = dict(
            text="Проверить тетради",
            school_class="9",
            deadline=date.today() + timedelta(days=2),
            is_done=False,
        )
        if "todo_type" in todo_cols:
            base["todo_type"] = "проверить работу"
        elif "topic" in todo_cols:
            base["topic"] = "проверить работу"
        db.add(TodoItem(**base))
        db.commit()
finally:
    db.close()
