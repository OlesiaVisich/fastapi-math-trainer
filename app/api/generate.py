"""Эндпоинт /api/generate: генерация заданий."""
import json
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.logic import generate_tasks
from app.models import Task as TaskModel, Worksheet as WorksheetModel
from app.schemas import GenerateRequest, GenerateResponse

router = APIRouter()


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate", response_model=GenerateResponse)
def generate_worksheet(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Генерирует карточку с заданиями."""
    tasks_data = generate_tasks(
        number_type=request.number_type,
        operations=request.operations,
        min_num=request.min_num,
        max_num=request.max_num,
        count=request.count,
        only_positive_answers=request.only_positive_answers,
        numbered_tasks=request.numbered_tasks,
    )

    settings_dict = {
        "number_type": request.number_type,
        "operations": request.operations,
        "min_num": request.min_num,
        "max_num": request.max_num,
        "count": request.count,
        "num_columns": request.num_columns,
        "only_positive_answers": request.only_positive_answers,
        "header_text": request.header_text,
        "numbered_tasks": request.numbered_tasks,
    }

    db_worksheet = WorksheetModel(
        title="Generated Worksheet",
        settings=json.dumps(settings_dict, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(db_worksheet)
    db.commit()
    db.refresh(db_worksheet)

    for i, task in enumerate(tasks_data):
        db_task = TaskModel(
            question=task.question,
            answer=task.answer,
            order_index=task.order_index,
            worksheet_id=db_worksheet.id,
        )
        db.add(db_task)
    db.commit()

    return GenerateResponse(
        worksheet_id=db_worksheet.id, tasks=tasks_data
    )