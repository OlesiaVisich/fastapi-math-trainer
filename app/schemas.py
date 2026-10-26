"""Pydantic-схемы для валидации данных."""
import datetime as dt_module
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class Token(BaseModel):
    """JWT-токен."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Данные пользователя из токена."""

    username: Optional[str] = None


class UserBase(BaseModel):
    """Базовая модель пользователя."""

    username: str
    email: str


class UserCreate(UserBase):
    """Создание пользователя."""

    password: str


class User(UserBase):
    """Пользователь с ID и метаданными."""

    id: int
    is_active: bool
    created_at: datetime

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class TaskSchema(BaseModel):
    """Задание (вопрос + ответ + порядок)."""

    question: str
    answer: str
    order_index: int


class WorksheetBase(BaseModel):
    """Базовая модель карточки."""

    title: Optional[str] = None
    settings: dict


class WorksheetCreate(WorksheetBase):
    """Создание карточки."""


class Worksheet(WorksheetBase):
    """Карточка с задачами."""

    id: int
    user_id: int
    created_at: datetime
    tasks: List[TaskSchema] = []

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class GenerateRequest(BaseModel):
    """Параметры генерации заданий."""

    number_type: Literal["natural", "integer", "fraction", "decimal"] = "integer"
    operations: List[Literal["+", "-", "*", "/"]] = ["+"]
    min_num: int = 1
    max_num: int = 10
    count: int = 10
    num_columns: int = 1
    only_positive_answers: bool = False
    header_text: Optional[str] = None
    numbered_tasks: bool = False


class GenerateResponse(BaseModel):
    """Ответ API: ID карточки и список задач."""

    worksheet_id: int
    tasks: List[TaskSchema]

class LessonBase(BaseModel):
    """Базовая модель урока."""

    topic: str
    description: Optional[str] = None
    date: Optional[dt_module.date] = None
    homework: Optional[str] = None


class LessonCreate(LessonBase):
    """Создание урока (поля формы + опциональный PDF-файл)."""


class Lesson(LessonBase):
    """Урок с ID, файлом задач и метаданными."""

    id: int
    user_id: Optional[int] = None
    pdf_filename: Optional[str] = None
    created_at: datetime

    class Config:
        """Конфигурация модели."""

        from_attributes = True
