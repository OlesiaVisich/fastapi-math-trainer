"""Главная точка входа FastAPI."""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.api import auth, users, worksheets, generate, lessons

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(worksheets.router, prefix="/worksheets", tags=["worksheets"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(lessons.router, prefix="/lessons", tags=["lessons"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.get("/", include_in_schema=False)
def index():
    """Главная страница сайта."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/lessons-page", include_in_schema=False)
def lessons_page():
    """Страница «Мои уроки»."""
    return FileResponse(os.path.join(STATIC_DIR, "lessons.html"))