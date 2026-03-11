from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from routers.services import router as services_router
from routers.availability import router as availability_router
from routers.appointments import router as appointments_router

app = FastAPI(title="Nail Appointment App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services_router)
app.include_router(availability_router)
app.include_router(appointments_router)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "app": "Nail Appointment API",
        "docs": "/docs",
        "endpoints": ["/services", "/availability", "/appointments"],
    }
