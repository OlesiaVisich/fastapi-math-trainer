"""Эндпоинты раздела «Задания»: создание, список, удаление, группы аналогов."""
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models import Assignment, AssignmentGroup
from app.schemas import Assignment as AssignmentSchema
from app.schemas import AssignmentGroupOut

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


def _to_schema(a: Assignment) -> dict:
    """Превращает ORM-объект задания в словарь ответа (с именем группы)."""
    return {
        "id": a.id,
        "school_class": a.school_class,
        "topic": a.topic,
        "difficulty": a.difficulty,
        "latex_code": a.latex_code,
        "group_id": a.group_id,
        "group_name": a.group.name if a.group else None,
        "created_at": a.created_at,
        "user_id": a.user_id,
    }


def _split_variants(raw: str) -> List[str]:
    """Разбивает введённый/загруженный текст на варианты заданий.

    Каждый непустой блок текста (строки, разделённые пустой строкой) —
    отдельный вариант. Обрамляющие $$...$$ сохраняются как есть.
    Переносы строк ВНУТРИ варианта сохраняются: у задания может быть
    несколько строк (условия, подпункты). Пробелы вокруг самих переводов
    строк убираются, чтобы не накапливались лишние отступы.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b.strip("\n").strip() for b in text.split("\n\n")]
    cleaned = []
    for b in blocks:
        if not b:
            continue
        # сохраняем структуру строк варианта, но без «висячих» пробелов
        b = re.sub(r"[ \t]*\n[ \t]*", "\n", b).strip()
        if b:
            cleaned.append(b)
    return cleaned


@router.post("/", response_model=List[AssignmentSchema])
async def create_assignments(
    request: Request,
    school_class: str = Form(...),
    topic: str = Form(...),
    difficulty: Optional[str] = Form(None),
    group_mode: Optional[str] = Form("none"),
    existing_group_id: Optional[int] = Form(None),
    new_group_name: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Создаёт одно задание или сразу несколько аналогов.

    Аналогичные задания передаются в поле latex_code (или в txt-файле):
    каждый блок текста, отделённый пустой строкой, становится отдельным
    заданием. group_mode: none | new (название новой группы) | existing (ID).

    Поле latex_code читается напрямую из формы (без строгой типизации),
    чтобы некорректный/пустой ввод не приводил к ошибке 422 без сообщения.
    """
    if not school_class.strip():
        raise HTTPException(status_code=400, detail="Класс не может быть пустым")
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Тема не может быть пустой")

    # Текст вариантов: из поля latex_code (браузер читает выбранный файл и
    # отправляет его содержимое текстом) либо из параметра file (например,
    # при отправке через Swagger UI / напрямую).
    form = await request.form()
    raw_text = ""
    latex_field = form.get("latex_code")
    if isinstance(latex_field, str):
        raw_text = latex_field
    elif latex_field is not None and hasattr(latex_field, "read"):
        # Браузер мог отправить textarea как файл — читаем его содержимое
        try:
            content = await latex_field.read()
            raw_text = content.decode("utf-8-sig", errors="replace")
        except Exception:
            raw_text = ""
    if (not raw_text.strip()) and file is not None and getattr(file, "filename", None):
        content = file.file.read()
        try:
            raw_text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raw_text = content.decode("cp1251", errors="replace")

    variants = _split_variants(raw_text)
    if not variants:
        raise HTTPException(status_code=400, detail="Добавьте LaTeX-код заданий (пустое поле не принимается)")

    # Определение группы аналогов
    group: Optional[AssignmentGroup] = None
    mode = (group_mode or "none").strip().lower()
    if mode == "new":
        name = (new_group_name or "").strip() or topic.strip()
        group = AssignmentGroup(name=name)
        db.add(group)
        db.flush()
    elif mode == "existing":
        if not existing_group_id:
            raise HTTPException(status_code=400, detail="Не указана существующая группа")
        group = (
            db.query(AssignmentGroup)
            .filter(AssignmentGroup.id == existing_group_id)
            .first()
        )
        if group is None:
            raise HTTPException(status_code=404, detail="Группа не найдена")

    diff = _validate_difficulty(difficulty)
    created = []
    for variant in variants:
        assignment = Assignment(
            school_class=school_class.strip(),
            topic=topic.strip(),
            difficulty=diff,
            latex_code=variant,
            group_id=group.id if group else None,
        )
        db.add(assignment)
        created.append(assignment)
    db.commit()
    for a in created:
        db.refresh(a)
    return [_to_schema(a) for a in created]


@router.get("/groups", response_model=List[AssignmentGroupOut])
def list_groups(db: Session = Depends(get_db)):
    """Список групп аналогов с количеством заданий (для выпадающего списка)."""
    groups = db.query(AssignmentGroup).order_by(AssignmentGroup.name).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "assignments_count": (
                db.query(Assignment).filter(Assignment.group_id == g.id).count()
            ),
        }
        for g in groups
    ]


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Удаляет группу аналогов; задания группы остаются, теряя метку аналога."""
    group = db.query(AssignmentGroup).filter(AssignmentGroup.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    db.query(Assignment).filter(Assignment.group_id == group_id).update(
        {"group_id": None}
    )
    db.delete(group)
    db.commit()
    return {"message": "Группа удалена"}


@router.get("/", response_model=List[AssignmentSchema])
def list_assignments(
    school_class: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    """Получает список заданий (раздел «Задания»), новые сверху.

    Параметры school_class, topic, difficulty и group_id фильтруют задания;
    используются в том числе в разделе «Конструктор работ».
    """
    query = db.query(Assignment).options(joinedload(Assignment.group))
    if school_class:
        query = query.filter(Assignment.school_class == school_class)
    if topic:
        query = query.filter(Assignment.topic == topic)
    if difficulty:
        query = query.filter(Assignment.difficulty == difficulty.strip().lower())
    if group_id:
        query = query.filter(Assignment.group_id == group_id)
    items = query.order_by(Assignment.id.desc()).offset(skip).limit(limit).all()
    return [_to_schema(a) for a in items]


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
        db.query(Assignment)
        .options(joinedload(Assignment.group))
        .filter(Assignment.id == assignment_id)
        .first()
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return _to_schema(assignment)


@router.put("/{assignment_id}", response_model=AssignmentSchema)
def update_assignment(
    assignment_id: int,
    school_class: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    latex_code: Optional[str] = Form(None),
    group_mode: Optional[str] = Form(None),
    existing_group_id: Optional[int] = Form(None),
    new_group_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Обновляет задание (класс, тема, сложность, LaTeX-код, группа аналогов)."""
    assignment = (
        db.query(Assignment)
        .options(joinedload(Assignment.group))
        .filter(Assignment.id == assignment_id)
        .first()
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
    # Изменение группы аналогов (none | new | existing)
    mode = (group_mode or "").strip().lower()
    if mode == "none":
        assignment.group_id = None
    elif mode == "new":
        name = (new_group_name or "").strip() or assignment.topic
        group = AssignmentGroup(name=name)
        db.add(group)
        db.flush()
        assignment.group_id = group.id
    elif mode == "existing":
        group = (
            db.query(AssignmentGroup)
            .filter(AssignmentGroup.id == existing_group_id)
            .first()
        ) if existing_group_id else None
        if group is None:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        assignment.group_id = group.id
    db.commit()
    db.refresh(assignment)
    return _to_schema(assignment)


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
