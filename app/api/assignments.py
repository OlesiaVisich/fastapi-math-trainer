"""Эндпоинты раздела «Задания»: создание, список, удаление."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Assignment
from app.schemas import Assignment as AssignmentSchema

router = APIRouter()

# Допустимые уровни сложности
DIFFICULTIES = ["простая", "средняя", "высокая"]


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_difficulty(value):
    """Проверяет, что сложность входит в допустимый список."""
    if value is None or not value.strip():
        return None
    v = value.strip().lower()
    if v not in DIFFICULTIES:
        raise HTTPException(
            status_code=400,
            detail="Недопустимая сложность. Варианты: " + ", ".join(DIFFICULTIES),
        )
    return v


@router.post("/", response_model=AssignmentSchema)
def create_assignment(
    school_class: str = Form(...),
    topic: str = Form(...),
    difficulty: Optional[str] = Form(None),
    latex_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Создаёт задание: класс, тема, сложность и LaTeX-код."""
    if not school_class.strip():
        raise HTTPException(status_code=400, detail="Класс не может быть пустым")
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Тема не может быть пустой")
    assignment = Assignment(
        school_class=school_class.strip(),
        topic=topic.strip(),
        difficulty=_validate_difficulty(difficulty),
        latex_code=(latex_code or "").strip() or None,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/", response_model=List[AssignmentSchema])
def list_assignments(
    school_class: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    """Получает список заданий (раздел «Задания»), новые сверху.

    Параметр school_class фильтрует задания по классу.
    """
    query = db.query(Assignment)
    if school_class:
        query = query.filter(Assignment.school_class == school_class)
    return query.order_by(Assignment.id.desc()).offset(skip).limit(limit).all()


@router.get("/difficulties")
def list_difficulties():
    """Возвращает допустимые уровни сложности для выпадающего списка."""
    return {"difficulties": DIFFICULTIES}


@router.get("/classes")
def list_classes(db: Session = Depends(get_db)):
    """Возвращает список классов, в которых есть задания (для разделов)."""
    rows = (
        db.query(Assignment.school_class)
        .filter(Assignment.school_class.isnot(None))
        .distinct()
        .all()
    )
    return {"classes": sorted(r[0] for r in rows)}


@router.get("/{assignment_id}", response_model=AssignmentSchema)
def read_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Получает задание по ID."""
    assignment = (
        db.query(Assignment).filter(Assignment.id == assignment_id).first()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentSchema)
def update_assignment(
    assignment_id: int,
    school_class: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    latex_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Обновляет задание (класс, тема, сложность, LaTeX-код)."""
    assignment = (
        db.query(Assignment).filter(Assignment.id == assignment_id).first()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    if school_class is not None:
        if not school_class.strip():
            raise HTTPException(status_code=400, detail="Класс не может быть пустым")
        assignment.school_class = school_class.strip()
    if topic is not None:
        if not topic.strip():
            raise HTTPException(status_code=400, detail="Тема не может быть пустой")
        assignment.topic = topic.strip()
    if difficulty is not None:
        assignment.difficulty = _validate_difficulty(difficulty)
    if latex_code is not None:
        assignment.latex_code = latex_code.strip() or None
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Удаляет задание."""
    assignment = (
        db.query(Assignment).filter(Assignment.id == assignment_id).first()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    db.delete(assignment)
    db.commit()
    return {"message": "Задание удалено"}
