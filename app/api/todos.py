"""Эндпоинты для списка дел: создание, список, изменение, удаление."""
import datetime as dt
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import TodoItem
from app.schemas import Todo

router = APIRouter()

# Допустимые типы дел (выбираются из выпадающего списка)
TODO_TYPES = ["встреча", "написать работу", "проверить работу", "ответить на письмо", "другое"]


def _validate_type(value):
    """Проверяет, что тип дела входит в допустимый список."""
    if value is None or not value.strip():
        return None
    v = value.strip().lower()
    if v not in TODO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый тип дела. Варианты: " + ", ".join(TODO_TYPES),
        )
    return v


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_deadline(value: Optional[str]):
    """Преобразует строку формы в date (пустая строка -> None)."""
    if value is None or not value.strip():
        return None
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата дедлайна")


@router.post("/", response_model=Todo)
def create_todo(
    text: str = Form(...),
    type: Optional[str] = Form(None),
    school_class: Optional[str] = Form(None),
    deadline: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Создаёт дело: текст, тип, класс и дедлайн."""
    todo = TodoItem(
        text=text.strip(),
        todo_type=_validate_type(type),
        school_class=(school_class or "").strip() or None,
        deadline=_parse_deadline(deadline),
    )
    if not todo.text:
        raise HTTPException(status_code=400, detail="Текст дела не может быть пустым")
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get("/", response_model=List[Todo])
def list_todos(
    school_class: Optional[str] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    """Получает список дел (раздел «Список дел»), новые сверху.

    Параметры school_class и type фильтруют дела по классу/типу.
    """
    query = db.query(TodoItem)
    if school_class:
        query = query.filter(TodoItem.school_class == school_class)
    if type:
        query = query.filter(TodoItem.todo_type == type.strip().lower())
    return query.order_by(TodoItem.id.desc()).offset(skip).limit(limit).all()


@router.get("/types")
def list_types():
    """Возвращает допустимые типы дел для выпадающего списка."""
    return {"types": TODO_TYPES}


@router.get("/classes")
def list_classes(db: Session = Depends(get_db)):
    """Возвращает список классов, в которых есть дела (для разделов в «Список дел»)."""
    rows = (
        db.query(TodoItem.school_class)
        .filter(TodoItem.school_class.isnot(None))
        .distinct()
        .all()
    )
    return {"classes": sorted(r[0] for r in rows)}


@router.get("/{todo_id}", response_model=Todo)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    """Получает дело по ID."""
    todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Дело не найдено")
    return todo


@router.put("/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    text: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    school_class: Optional[str] = Form(None),
    deadline: Optional[str] = Form(None),
    is_done: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
):
    """Обновляет дело (текст, тип, класс, дедлайн, статус выполнения)."""
    todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Дело не найдено")
    if text is not None:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Текст дела не может быть пустым")
        todo.text = text.strip()
    if type is not None:
        todo.todo_type = _validate_type(type)
    if school_class is not None:
        todo.school_class = school_class.strip() or None
    if deadline is not None:
        todo.deadline = _parse_deadline(deadline)
    if is_done is not None:
        todo.is_done = is_done
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Удаляет дело."""
    todo = db.query(TodoItem).filter(TodoItem.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Дело не найдено")
    db.delete(todo)
    db.commit()
    return {"message": "Дело удалено"}
