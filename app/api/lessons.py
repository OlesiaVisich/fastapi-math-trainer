"""Эндпоинты для работы с уроками: создание, список, файлы, удаление."""
import os
import re
import uuid
from datetime import date as dt_date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import LESSON_TYPES
from app.models import Lesson as LessonModel
from app.models import LessonFile
from app.schemas import Lesson

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "lessons")

ALLOWED_EXTENSIONS = {".pdf", ".pptx"}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument."
             "presentationml.presentation",
}


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_lesson_type(lesson_type: Optional[str]) -> Optional[str]:
    """Проверяет, что тип урока входит в допустимый список."""
    value = (lesson_type or "").strip().lower()
    if not value:
        return None
    if value not in LESSON_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Недопустимый тип урока. Выберите один из: "
                + ", ".join(LESSON_TYPES)
            ),
        )
    return value


def _parse_date(value: Optional[str]) -> Optional[dt_date]:
    """Преобразует строку формы в дату (пустая строка -> None)."""
    if value is None or not value.strip():
        return None
    try:
        return dt_date.fromisoformat(value.strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата урока")


def _save_file(file: UploadFile) -> dict:
    """Сохраняет файл урока (PDF или PPTX) на диск.

    Возвращает словарь с данными для записи в таблицу lesson_files.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Допустимы только файлы PDF и PPTX, получен формат: {ext or 'без расширения'}",
        )
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {
        "stored_name": stored_name,
        "original_name": file.filename,
        "content_type": CONTENT_TYPES.get(ext, file.content_type),
    }


def _attach_files(lesson: LessonModel, files: List[UploadFile]):
    """Сохраняет переданные файлы и привязывает их к уроку."""
    for file in files or []:
        if not file or not file.filename:
            continue
        data = _save_file(file)
        lesson.files.append(LessonFile(**data))
        # Совместимость со старым полем: первый PDF дублируется в pdf_filename
        if not lesson.pdf_filename and data["stored_name"].lower().endswith(".pdf"):
            lesson.pdf_filename = data["stored_name"]


@router.get("/types")
def list_lesson_types():
    """Возвращает допустимые типы уроков для выпадающего списка."""
    return {"types": LESSON_TYPES}


@router.post("/", response_model=Lesson)
def create_lesson(
    topic: str = Form(...),
    lesson_type: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    school_class: Optional[str] = Form(None),
    homework: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    tasks_pdf: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Создаёт урок: тип, дата, тема, описание, класс, домашняя работа, файлы.

    Можно передать несколько файлов через поле `files` (PDF и/или PPTX).
    Поле `tasks_pdf` оставлено для обратной совместимости.
    """
    lesson = LessonModel(
        topic=topic.strip(),
        lesson_type=_validate_lesson_type(lesson_type),
        date=_parse_date(date),
        description=(description or "").strip() or None,
        school_class=(school_class or "").strip() or None,
        homework=(homework or "").strip() or None,
    )
    upload_list = _collect_files(files)
    if tasks_pdf and (getattr(tasks_pdf, "filename", "") or "").strip():
        upload_list.insert(0, tasks_pdf)
    _attach_files(lesson, upload_list)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def _collect_files(files):
    """Оставляет только реально выбранные файлы из списка загрузки.

    Пустой выбор в <input type=file multiple> присылает один элемент с
    пустым именем — его пропускаем, чтобы не отдавать ошибку 422.
    """
    result = []
    for f in files or []:
        if f is None:
            continue
        name = (getattr(f, "filename", "") or "").strip()
        size = getattr(f, "size", None)
        if not name and not size:
            continue  # пустой выбор в <input type=file>
        result.append(f)
    return result


@router.post("/create", include_in_schema=False)
def create_lesson_form(
    topic: str = Form(""),
    lesson_type: Optional[str] = Form(None),
    date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    school_class: Optional[str] = Form(None),
    homework: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    tasks_pdf: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Создание урока из обычной HTML-формы (работает без JavaScript).

    После создания перенаправляет обратно на страницу «Мои уроки».
    """
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Укажите тему урока")
    lesson = LessonModel(
        topic=topic.strip(),
        lesson_type=_validate_lesson_type(lesson_type),
        date=_parse_date(date),
        description=(description or "").strip() or None,
        school_class=(school_class or "").strip() or None,
        homework=(homework or "").strip() or None,
    )
    upload_list = _collect_files(files)
    if tasks_pdf and (getattr(tasks_pdf, "filename", "") or "").strip():
        upload_list.insert(0, tasks_pdf)
    _attach_files(lesson, upload_list)
    db.add(lesson)
    db.commit()
    return RedirectResponse(url="/lessons-page", status_code=303)


@router.get("/", response_model=List[Lesson])
def list_lessons(
    school_class: Optional[str] = None,
    lesson_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Получает список уроков (раздел «Мои уроки»), новые сверху.

    Параметры school_class и lesson_type фильтруют уроки по классу и типу.
    """
    query = db.query(LessonModel)
    if school_class:
        query = query.filter(LessonModel.school_class == school_class)
    if lesson_type:
        query = query.filter(LessonModel.lesson_type == lesson_type.lower())
    return query.order_by(LessonModel.id.desc()).offset(skip).limit(limit).all()


@router.get("/classes")
def list_classes(db: Session = Depends(get_db)):
    """Возвращает список классов, в которых есть уроки (для разделов в «Моих уроках»)."""
    rows = (
        db.query(LessonModel.school_class)
        .filter(LessonModel.school_class.isnot(None))
        .distinct()
        .all()
    )
    return {"classes": sorted(r[0] for r in rows)}


@router.get("/{lesson_id}", response_model=Lesson)
def read_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Получает урок по ID."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return lesson


@router.get("/{lesson_id}/files")
def list_lesson_files(lesson_id: int, db: Session = Depends(get_db)):
    """Возвращает список прикреплённых файлов урока."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    return {
        "files": [
            {
                "id": f.id,
                "name": f.original_name,
                "content_type": f.content_type,
            }
            for f in lesson.files
        ]
    }


@router.get("/{lesson_id}/files/{file_id}")
def download_lesson_file(
    lesson_id: int, file_id: int, db: Session = Depends(get_db)
):
    """Скачивает прикреплённый к уроку файл (PDF или PPTX)."""
    record = (
        db.query(LessonFile)
        .filter(LessonFile.id == file_id, LessonFile.lesson_id == lesson_id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Файл не найден")
    path = os.path.join(UPLOAD_DIR, record.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    return FileResponse(
        path, media_type=record.content_type, filename=record.original_name
    )


@router.get("/{lesson_id}/pdf")
def download_lesson_pdf(lesson_id: int, db: Session = Depends(get_db)):
    """Скачивает первый PDF-файл урока (обратная совместимость со старой ссылкой)."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    pdf_file = next(
        (f for f in lesson.files if f.original_name.lower().endswith(".pdf")), None
    )
    if pdf_file is None and lesson.pdf_filename:
        path = os.path.join(UPLOAD_DIR, lesson.pdf_filename)
        if os.path.exists(path):
            return FileResponse(path, media_type="application/pdf",
                                filename=lesson.pdf_filename)
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    if pdf_file is None:
        raise HTTPException(status_code=404, detail="PDF-файл к уроку не прикреплён")
    path = os.path.join(UPLOAD_DIR, pdf_file.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    return FileResponse(
        path, media_type="application/pdf", filename=pdf_file.original_name
    )


@router.delete("/{lesson_id}")
def delete_lesson(lesson_id: int, db: Session = Depends(get_db)):
    """Удаляет урок вместе с прикреплёнными файлами."""
    lesson = db.query(LessonModel).filter(LessonModel.id == lesson_id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Урок не найден")
    for record in list(lesson.files):
        path = os.path.join(UPLOAD_DIR, record.stored_name)
        if os.path.exists(path):
            os.remove(path)
    if lesson.pdf_filename:
        path = os.path.join(UPLOAD_DIR, lesson.pdf_filename)
        if os.path.exists(path):
            os.remove(path)
    db.delete(lesson)
    db.commit()
    return {"message": "Урок удалён"}
