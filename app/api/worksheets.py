"""Эндпоинты для работы с карточками: CRUD."""
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import Task as TaskModel, Worksheet as WorksheetModel
from app.schemas import Worksheet

router = APIRouter()


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{worksheet_id}", response_model=Worksheet)
def read_worksheet(
    worksheet_id: int, db: Session = Depends(get_db)
):
    """Получает карточку по ID."""
    worksheet = db.query(WorksheetModel).filter(
        WorksheetModel.id == worksheet_id
    ).first()
    if worksheet is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    worksheet.settings = json.loads(worksheet.settings)

    tasks = db.query(TaskModel).filter(
        TaskModel.worksheet_id == worksheet_id
    ).order_by(TaskModel.order_index).all()
    worksheet.tasks = tasks
    return worksheet


@router.get("/", response_model=List[Worksheet])
def list_worksheets(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    """Получает список карточек."""
    worksheets = db.query(WorksheetModel).offset(skip).limit(limit).all()
    for ws in worksheets:
        ws.settings = json.loads(ws.settings)
        tasks = db.query(TaskModel).filter(
            TaskModel.worksheet_id == ws.id
        ).order_by(TaskModel.order_index).all()
        ws.tasks = tasks
    return worksheets


@router.delete("/{worksheet_id}")
def delete_worksheet(
    worksheet_id: int, db: Session = Depends(get_db)
):
    """Удаляет карточку по ID."""
    worksheet = db.query(WorksheetModel).filter(
        WorksheetModel.id == worksheet_id
    ).first()
    if worksheet is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")

    db.delete(worksheet)
    db.commit()
    return {"message": "Worksheet deleted"}