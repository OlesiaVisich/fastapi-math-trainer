from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///./test.db"

settings = Settings()