"""Модуль аутентификации: хеширование, JWT, проверка пользователей."""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import User as UserModel
from app.database import SessionLocal
from app.config import settings
from app.schemas import TokenData

# Заменяем pwd_context на встроенное хеширование
'''def get_password_hash(password):
    # Хешируем пароль с помощью SHA256
    return hashlib.sha256(password.encode()).hexdigest()'''

'''def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password'''

'''def get_user_by_username(db: Session, username: str):
    return db.query(UserModel).filter(UserModel.username == username).first()'''

'''def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user'''

'''def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
):
    """
    Создаёт JWT токен для пользователя.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt'''


async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login")),
    db: Session = Depends(lambda: SessionLocal()),
) -> UserModel:
    """Получает текущего пользователя по токену (временная заглушка)."""
    # ⚠️ Временная заглушка: всегда возвращаем пользователя testuser_new
    user = db.query(UserModel).filter(
        UserModel.username == "testuser_new"
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user