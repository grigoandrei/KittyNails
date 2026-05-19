from fastapi import FastAPI
from src.routers.appointments import router as appointments_router

app = FastAPI()
app.include_router(appointments_router)

@app.get("/")
def health_check():
    return {"status": "ok"}