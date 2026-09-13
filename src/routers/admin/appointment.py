import asyncio
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_admin
from src.database import get_db
from src.models.appointment import Appointment, Status
from src.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from src.services.appointment_service import (
    create_appointment,
    list_appointments,
    update_appointment,
    update_appointment_status,
)
from src.services.s3_service import generate_presigned_url

router = APIRouter(prefix="/api/admin/appointments", tags=["admin-appointments"], dependencies=[Depends(get_current_admin)])


def _to_response(appointment: Appointment, image_url: str | None) -> AppointmentResponse:
    response = AppointmentResponse.model_validate(appointment)
    response.image_url = image_url
    return response


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_manual_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Admin-created booking for a client who arranged via Instagram.

    Creates a BOOKED appointment directly (no Stripe deposit) with
    source="instagram". Goes through the same slot/conflict/working-hours
    logic as public bookings. No confirmation email is sent — the client
    already coordinated with the artist directly.
    """
    appointment = await create_appointment(
        data, db, status=Status.BOOKED, source="instagram"
    )
    return _to_response(appointment, None)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def edit_appointment(
    appointment_id: UUID,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    """Edit an appointment's start time, duration, and/or removal flag.

    Duration is an explicit override (end_time = start + duration); price is
    re-derived from the service + removal. Re-runs availability / hours /
    blocked / conflict checks (excluding this appointment).
    """
    appointment = await update_appointment(db, appointment_id, data)
    image_url = await asyncio.to_thread(generate_presigned_url, appointment.image_key)
    return _to_response(appointment, image_url)


@router.get("/", response_model=list[AppointmentResponse])
async def get_appointment(
    status: Status | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    appointments = await list_appointments(
        db, status=status, date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )
    # Presign each stored photo so the admin can view it from the private bucket.
    # boto3 is blocking, so generate URLs off the event loop.
    image_urls = await asyncio.gather(
        *(asyncio.to_thread(generate_presigned_url, a.image_key) for a in appointments)
    )
    return [_to_response(a, url) for a, url in zip(appointments, image_urls)]

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):  # noqa: B008
    return await update_appointment_status(db, appointment_id, Status.CANCELED)

@router.patch("/{appointment_id}/no-show", response_model=AppointmentResponse)
async def no_show_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):  # noqa: B008
    return await update_appointment_status(db, appointment_id, Status.NO_SHOW)

@router.patch("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):  # noqa: B008
    return await update_appointment_status(db, appointment_id, Status.COMPLETED)
