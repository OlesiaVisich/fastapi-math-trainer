"""Конфигурация приложения."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки проекта."""

    SECRET_KEY: str = "my_very_secret_key_1234567890"
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///./test.db"


settings = Settings()