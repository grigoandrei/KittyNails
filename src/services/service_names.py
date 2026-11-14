"""Human-readable service names for emails, Telegram and Stripe."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.appointment import Appointment
from src.models.design_tier import DesignTier
from src.models.monthly_set_model import MonthlySetModel
from src.models.nail_type import NailType

FALLBACK_NAME = "Nail Service"


async def resolve_service_names(
    appointment: Appointment, db: AsyncSession
) -> tuple[str, str | None]:
    """Return (service name, design tier name or None) for an appointment.

    Monthly set bookings read as "Monthly set: <title>" and never have a tier.
    """
    if appointment.monthly_set_model_id is not None:
        result = await db.execute(
            select(MonthlySetModel.title).where(
                MonthlySetModel.id == appointment.monthly_set_model_id
            )
        )
        title = result.scalar_one_or_none()
        return (f"Monthly set: {title}" if title else "Monthly set"), None

    result = await db.execute(
        select(NailType.name).where(NailType.id == appointment.nail_type_id)
    )
    nail_type_name = result.scalar_one_or_none() or FALLBACK_NAME

    design_tier_name = None
    if appointment.design_tier_id:
        result = await db.execute(
            select(DesignTier.name).where(DesignTier.id == appointment.design_tier_id)
        )
        design_tier_name = result.scalar_one_or_none()

    return nail_type_name, design_tier_name
