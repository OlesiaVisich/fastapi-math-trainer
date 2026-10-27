from app.database import engine, Base
from app.models import User, Worksheet, Task, Lesson, TodoItem

print("Создаём таблицы...")
Base.metadata.create_all(bind=engine)
print("✅ Таблицы успешно созданы в", engine.url)