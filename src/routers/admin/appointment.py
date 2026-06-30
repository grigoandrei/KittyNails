from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.appointment import AppointmentResponse
from src.services.appointment_service import list_appointments, update_appointment_status
from src.models.appointment import Status
from datetime import date
from uuid import UUID

router = APIRouter(prefix="/api/admin/appointments", tags=["admin-appointments"])

@router.get("/", response_model=list[AppointmentResponse])
async def get_appointment(
    status: Status | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db)
):
    return await list_appointments(db, status=status, date_from=date_from, date_to=date_to)

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):
    return await update_appointment_status(db, appointment_id, Status.CANCELED)

@router.patch("/{appointment_id}/no-show", response_model=AppointmentResponse)
async def no_show_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):
    return await update_appointment_status(db, appointment_id, Status.NO_SHOW)

@router.patch("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):
    return await update_appointment_status(db, appointment_id, Status.COMPLETED)