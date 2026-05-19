from src.schemas.appointment import AppointmentCreate, AppointmentResponse
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.appointment_service import create_appointment

router = APIRouter()

@router.post("/api/appointments", response_model=AppointmentResponse, status_code=201)
async def create(data: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    try:
        appointment = await create_appointment(data, db)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=409, detail=str(e))
        

    return appointment