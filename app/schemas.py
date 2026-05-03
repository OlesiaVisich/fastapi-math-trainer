from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TaskSchema(BaseModel):
    question: str
    answer: str
    order_index: int

class WorksheetBase(BaseModel):
    title: Optional[str] = None
    settings: dict  # JSON-like structure

class WorksheetCreate(WorksheetBase):
    pass

class Worksheet(WorksheetBase):
    id: int
    user_id: int
    created_at: datetime
    tasks: List[TaskSchema] = []

    class Config:
        from_attributes = True

class GenerateRequest(BaseModel):
    number_type: Literal['natural', 'integer', 'fraction', 'decimal'] = 'integer'
    operations: List[Literal['+', '-', '*', '/']] = ['+']
    min_num: int = 1
    max_num: int = 10
    count: int = 10
    num_columns: int = 1
    only_positive_answers: bool = False
    header_text: Optional[str] = None
    numbered_tasks: bool = False

class GenerateResponse(BaseModel):
    worksheet_id: int
    tasks: List[TaskSchema]