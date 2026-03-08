from fastapi import FastAPI
from db.database import Base, engine, SessionLocal
from db import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

Base.metadata.create_all(bind=engine)

