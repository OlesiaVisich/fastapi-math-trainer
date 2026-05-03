from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Worksheet as WorksheetModel, Task as TaskModel, User as UserModel
from app.schemas import Worksheet, WorksheetCreate
from app.auth import get_current_user
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[Worksheet])
def read_worksheets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    worksheets = db.query(WorksheetModel).offset(skip).limit(limit).all()
    return worksheets

@router.post("/", response_model=Worksheet)
def create_worksheet(worksheet: WorksheetCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_worksheet = WorksheetModel(**worksheet.dict(), user_id=current_user.id)
    db.add(db_worksheet)
    db.commit()
    db.refresh(db_worksheet)
    return db_worksheet

@router.get("/{worksheet_id}", response_model=Worksheet)
def read_worksheet(worksheet_id: int, db: Session = Depends(get_db)):
    worksheet = db.query(WorksheetModel).filter(WorksheetModel.id == worksheet_id).first()
    if worksheet is None:
        raise HTTPException(status_code=404, detail="Worksheet not found")
    # Загружаем задачи
    tasks = db.query(TaskModel).filter(TaskModel.worksheet_id == worksheet_id).order_by(TaskModel.order_index).all()
    worksheet.tasks = tasks
    return worksheet

@router.delete("/{worksheet_id}")
def delete_worksheet(worksheet_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    worksheet = db.query(WorksheetModel).filter(WorksheetModel.id == worksheet_id).first()
    if worksheet is None or worksheet.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Worksheet not found or not owned")
    db.delete(worksheet)
    db.commit()
    return {"message": "Worksheet deleted"}