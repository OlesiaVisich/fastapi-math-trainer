from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "super-secret-key"
    DATABASE_URL: str = "sqlite:///./test.db"

settings = Settings()