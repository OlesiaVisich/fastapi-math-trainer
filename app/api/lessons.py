"""Эндпоинты для работы с уроками: создание, список, просмотр, удаление."""
import os
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Lesson as LessonModel
from app.schemas import Lesson

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "lessons")


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _save_pdf(file: UploadFile) -> str:
    """Сохраняет PDF-файл с задачами на диск и возвращает имя сохранённого файла."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Файл с задачами должен быть в формате PDF"
        )
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return stored_name


@router.post("/", response_model=Lesson)
def create_lesson(
    topic: str = Form(...),
    description: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    homework: Optional[str] = Form(None),
    tasks_pdf: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Создаёт урок: тема, текстовое описание, дата, домашняя работа, PDF с задачами."""
    lesson = LessonModel(
        topic=topic,
        description=description,
        homework=homework,
    )
    if date:
        from datetime import datetime as dt

        try:
            lesson.date = dt.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Неверный формат даты. Ожидается ГГГГ-ММ-ДД",
            )
    if tasks_pdf and tasks_pdf.filename:
        lesson.pdf_filename = _save_pdf(tasks_pdf)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/", response_model=List[Lesson])
def list_lessons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получает список уроков (раздел «Мои уроки»), новые сверху."""
    return (
        db.query(LessonModel).order_by(LessonModel.id.desc()).offset(skip).limit(limit).all()
    )


@router.get("/{lesson_id}", response_model=Lesson)
def read_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Получает урок по ID."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return lesson


@router.get("/{lesson_id}/pdf")
def download_lesson_pdf(lesson_id: int, db: Session = Depends(get_db)):
    """Скачивает PDF-файл с задачами урока."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    if not lesson.pdf_filename:
        raise HTTPException(status_code=404, detail="PDF-файл к уроку не прикреплён")
    path = os.path.join(UPLOAD_DIR, lesson.pdf_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    return FileResponse(path, media_type="application/pdf", filename=lesson.pdf_filename)


@router.delete("/{lesson_id}")
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Удаляет урок вместе с прикреплённым PDF-файлом."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    if lesson.pdf_filename:
        path = os.path.join(UPLOAD_DIR, lesson.pdf_filename)
        if os.path.exists(path):
            os.remove(path)
    db.delete(lesson)
    db.commit()
    return {"message": "Урок удалён"}
