"""Модели базы данных: User, Worksheet, Task, Lesson, TodoItem."""
from datetime import datetime

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

class Lesson(Base):
    """Урок учителя: тема, описание, класс, домашняя работа, PDF с задачами."""

    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    school_class = Column(String, nullable=True, index=True)
    homework = Column(Text, nullable=True)
    pdf_filename = Column(String, nullable=True)
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
