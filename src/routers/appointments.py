from src.schemas.appointment import AppointmentCreate, AppointmentResponse
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.appointment_service import create_appointment
from src.limiter import limiter

router = APIRouter()

@router.post("/api/appointments", response_model=AppointmentResponse, status_code=201)
@limiter.limit("10/hour")
async def create(request: Request, data: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    return await create_appointment(data, db)