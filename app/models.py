"""Модели базы данных: User, Worksheet, Task, Lesson, TodoItem."""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """Пользователь системы."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class Worksheet(Base):
    """Карточка заданий."""

    __tablename__ = "worksheets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    settings = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))


class Task(Base):
    """Задание (вопрос + ответ + порядок)."""

    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    order_index = Column(Integer, nullable=False)
    worksheet_id = Column(Integer, ForeignKey("worksheets.id"))

LESSON_TYPES = [
    "урок с презентацией",
    "урок с листочком",
    "практическая/самостоятельная работа",
    "контрольная работа",
]


class LessonFile(Base):
    """Файл, прикреплённый к уроку (PDF или PPTX).

    role: main — основной файл урока (презентация / листочек / работа / контрольная),
          keys — ключи для проверки,
          other — прочие файлы.
    """

    __tablename__ = "lesson_files"
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), index=True)
    stored_name = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    role = Column(String, nullable=True, default="other")
    created_at = Column(DateTime, default=datetime.utcnow)


class Lesson(Base):
    """Урок учителя: тип, тема, описание, класс, домашняя работа, файлы."""

    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    lesson_type = Column(String, nullable=True, index=True)
    date = Column(Date, nullable=True, index=True)  # дата проведения урока
    description = Column(Text, nullable=True)
    school_class = Column(String, nullable=True, index=True)
    homework = Column(Text, nullable=True)
    pdf_filename = Column(String, nullable=True)  # устаревшее: первый файл
    files = relationship(
        "LessonFile", backref="lesson", cascade="all, delete-orphan"
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))


class TodoItem(Base):
    """Дело учителя: текст, тип, класс, дедлайн, статус выполнения."""

    __tablename__ = "todo_items"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    todo_type = Column(String, nullable=True, index=True)
    school_class = Column(String, nullable=True, index=True)
    deadline = Column(Date, nullable=True, index=True)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))


class AssignmentGroup(Base):
    """Группа аналогов заданий (например, 30 уравнений одного типа)."""

    __tablename__ = "assignment_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    assignments = relationship(
        "Assignment", back_populates="group", cascade="all, delete-orphan"
    )


class Assignment(Base):
    """Задание для учеников: класс, тема, сложность, LaTeX-код, группа аналогов."""

    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    school_class = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=True, index=True)
    latex_code = Column(Text, nullable=True)
    group_id = Column(
        Integer, ForeignKey("assignment_groups.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    group = relationship("AssignmentGroup", back_populates="assignments")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
