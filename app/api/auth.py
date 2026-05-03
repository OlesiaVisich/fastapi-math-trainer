"""Эндпоинты аутентификации."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import User as UserModel
from app.schemas import User, UserCreate

router = APIRouter()


def get_db():
    """Получает сессию базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрирует нового пользователя."""
    existing_user = db.query(UserModel).filter(
        UserModel.username == user.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username already registered"
        )
    existing_email = db.query(UserModel).filter(
        UserModel.email == user.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=400, detail="Email already registered"
        )

    hashed_password = "hashed_" + user.password  # Заглушка
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Вход пользователя и получение токена."""
    user = db.query(UserModel).filter(
        UserModel.username == form_data.username
    ).first()
    if not user or user.hashed_password != "hashed_" + form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = "fake_token_for_" + form_data.username
    return {"access_token": access_token, "token_type": "bearer"}