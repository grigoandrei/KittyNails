import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.limiter import limiter
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.schemas.appointment import AppointmentCreate, AppointmentResponse
from src.services.appointment_service import create_appointment
from src.services.email_service import send_confirmation_email

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/appointments", response_model=AppointmentResponse, status_code=201)
@limiter.limit("10/hour")
async def create(
    request: Request,
    data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    appointment = await create_appointment(data, db)

    # Look up names for the confirmation email (best-effort, non-blocking)
    try:
        nail_type_result = await db.execute(
            select(NailType).where(NailType.id == appointment.nail_type_id)
        )
        nail_type = nail_type_result.scalar_one_or_none()
        nail_type_name = nail_type.name if nail_type else "Nail Service"

        design_tier_name = None
        if appointment.design_tier_id:
            dt_result = await db.execute(
                select(DesignTier).where(DesignTier.id == appointment.design_tier_id)
            )
            design_tier = dt_result.scalar_one_or_none()
            design_tier_name = design_tier.name if design_tier else None

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

    return appointment
