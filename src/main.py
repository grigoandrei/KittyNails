from fastapi import FastAPI
from src.routers.appointments import router as appointments_router
from src.routers.admin.services import router as admin_services_router
from src.routers.services import router as services_router
from src.routers.admin.availability import router as admin_availability_router
from src.routers.admin.blocked_time import router as blocked_time_router
from src.routers.admin.appointment import router as admin_appointments_router
from src.routers.slots import router as slots_router
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://localhost:3000"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(appointments_router)
app.include_router(admin_services_router)
app.include_router(services_router)
app.include_router(admin_availability_router)
app.include_router(blocked_time_router)
app.include_router(admin_appointments_router)
app.include_router(slots_router)

@app.get("/")
def health_check():
    return {"status": "ok"}