from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import GenerateRequest, GenerateResponse, WorksheetCreate
from app.models import Worksheet as WorksheetModel, Task as TaskModel
from app.logic import generate_tasks
from app.auth import get_current_user
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate", response_model=GenerateResponse)
def generate_worksheet(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Генерирует карточку с заданиями.
    """
    tasks = generate_tasks(
        number_type=request.number_type,
        operations=request.operations,
        min_num=request.min_num,
        max_num=request.max_num,
        count=request.count,
        only_positive_answers=request.only_positive_answers,
        numbered_tasks=request.numbered_tasks
    )

    # Сохраняем карточку и задачи в БД
    worksheet_data = WorksheetCreate(
        title=request.header_text or "Generated Worksheet",
        settings=request.dict()
    )
    import json

    # Преобразуем словарь в строку
    worksheet_data_dict = worksheet_data.dict()
    worksheet_data_dict["settings"] = json.dumps(worksheet_data_dict["settings"], ensure_ascii=False)

    db_worksheet = WorksheetModel(**worksheet_data_dict, user_id=current_user.id)
    db.add(db_worksheet)
    db.flush()  # Чтобы получить ID

    for t in tasks:
        db_task = TaskModel(
            worksheet_id=db_worksheet.id,
            question=t.question,
            answer=t.answer,
            order_index=t.order_index
        )
        db.add(db_task)

    db.commit()
    db.refresh(db_worksheet)

    return GenerateResponse(worksheet_id=db_worksheet.id, tasks=tasks)