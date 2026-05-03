from fastapi import FastAPI
from app.api import auth

app = FastAPI(title="Math Trainer API")

# Подключаем маршруты
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Math Trainer API"}