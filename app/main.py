from fastapi import FastAPI
from app.api import auth, users, worksheets, generate

app = FastAPI(title="Math Trainer API")

# Подключаем маршруты
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(worksheets.router, prefix="/worksheets", tags=["worksheets"])
app.include_router(generate.router, prefix="/api", tags=["generate"])

@app.get("/")
def read_root():
    return {"message": "Math Trainer API"}