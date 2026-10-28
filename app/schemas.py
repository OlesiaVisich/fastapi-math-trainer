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
    lesson_type: Optional[str] = None
    # ВАЖНО: аннотация через dt_module.date, а не через локальное имя `date`:
    # поле с именем `date` затеняет импорт datetime.date при вычислении
    # аннотаций класса (pydantic иначе получает NoneType и падает с ошибкой
    # "Input should be None" на валидации ответа).
    date: Optional[dt_module.date] = None
    description: Optional[str] = None
    school_class: Optional[str] = None
    homework: Optional[str] = None


class LessonFileOut(BaseModel):
    """Прикреплённый к уроку файл."""

    id: int
    original_name: str
    content_type: Optional[str] = None
    role: Optional[str] = "other"

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class LessonCreate(LessonBase):
    """Создание урока (поля формы + опциональные файлы)."""


class Lesson(LessonBase):
    """Урок с ID, прикреплёнными файлами и метаданными."""

    id: int
    user_id: Optional[int] = None
    pdf_filename: Optional[str] = None
    files: List[LessonFileOut] = []
    created_at: datetime

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class TodoBase(BaseModel):
    """Базовая модель дела."""

    text: str
    todo_type: Optional[str] = None
    school_class: Optional[str] = None
    deadline: Optional[date] = None


class TodoCreate(TodoBase):
    """Создание дела."""


class TodoUpdate(BaseModel):
    """Обновление дела (все поля опциональны)."""

    text: Optional[str] = None
    todo_type: Optional[str] = None
    school_class: Optional[str] = None
    deadline: Optional[date] = None
    is_done: Optional[bool] = None


class Todo(TodoBase):
    """Дело с ID и статусом выполнения."""

    id: int
    user_id: Optional[int] = None
    is_done: bool = False
    created_at: datetime

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class AssignmentBase(BaseModel):
    """Базовая модель задания для учеников."""

    school_class: str
    topic: str
    difficulty: Optional[str] = None
    latex_code: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Создание задания."""


class AssignmentGroupOut(BaseModel):
    """Группа аналогов заданий."""

    id: int
    name: str
    assignments_count: int = 0

    class Config:
        """Конфигурация модели."""

        from_attributes = True


class Assignment(AssignmentBase):
    """Задание с ID и метаданными."""

    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        """Конфигурация модели."""

        from_attributes = True
