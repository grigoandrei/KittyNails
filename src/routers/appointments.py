import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.limiter import limiter
from src.schemas.appointment import AppointmentCreate, AppointmentResponse
from src.services.appointment_service import create_appointment
from src.services.booking_notifier import new_booking_message
from src.services.email_service import send_confirmation_email
from src.services.service_names import resolve_service_names
from src.services.telegram_service import send_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/appointments", response_model=AppointmentResponse, status_code=201)
@limiter.limit("10/hour")
async def create(
    request: Request,
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    appointment = await create_appointment(data, db)

    # Look up names for the confirmation email (best-effort, non-blocking)
    try:
        nail_type_name, design_tier_name = await resolve_service_names(
            appointment, db
        )

        background_tasks.add_task(
            send_confirmation_email,
            client_email=appointment.client_email,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            nail_type_name=nail_type_name,
            design_tier_name=design_tier_name,
            quoted_price=float(appointment.quoted_price),
        )
    except Exception as e:  # noqa: BLE001
        # Never let email failures break the booking
        logger.error("Failed to queue confirmation email: %s", str(e))

    message = await new_booking_message(appointment, db)
    if message:
        background_tasks.add_task(send_message, message)

    return appointment
