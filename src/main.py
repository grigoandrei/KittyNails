from fastapi import FastAPI
from db.database import Base, engine
from routers.services import router as services_router

app = FastAPI()
app.include_router(services_router)

Base.metadata.create_all(bind=engine)

