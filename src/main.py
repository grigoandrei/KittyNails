from fastapi import FastAPI
from src.routers.appointments import router as appointments_router
from src.routers.admin.services import router as admin_services_router
from src.routers.services import router as services_router

app = FastAPI()
app.include_router(appointments_router)
app.include_router(admin_services_router)
app.include_router(services_router)

@app.get("/")
def health_check():
    return {"status": "ok"}