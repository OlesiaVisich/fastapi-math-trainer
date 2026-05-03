"""Модели базы данных: User, Worksheet, Task."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
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