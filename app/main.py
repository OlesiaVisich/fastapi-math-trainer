from fastapi import FastAPI

app = FastAPI(title="Math Trainer API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Math Trainer API"}