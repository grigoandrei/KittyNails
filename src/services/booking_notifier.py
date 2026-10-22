"""Telegram ping to the artist whenever a new booking is confirmed.

Fires for paid web bookings (Stripe webhook), direct bookings, and admin
manual bookings. Fault-tolerant: a failure here must never break a booking.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.appointment import Appointment
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.services.telegram_service import (
    BERLIN_TZ,
    format_appointment_line,
    send_message,
)

logger = logging.getLogger(__name__)

_SOURCE_LABELS = {"web": "Website", "instagram": "Instagram"}


def build_new_booking_message(
    appointment: Appointment,
    nail_type_name: str,
    design_tier_name: str | None,
) -> str:
    """Pure formatter — no DB — so it's easy to test."""
    source = _SOURCE_LABELS.get(appointment.source, appointment.source)
    day = appointment.start_time.astimezone(BERLIN_TZ).strftime("%A, %B %d")
    line = format_appointment_line(
        appointment.start_time,
        nail_type_name,
        design_tier_name,
        appointment.needs_removal,
        float(appointment.quoted_price),
        appointment.client_email,
    )
    return f"<b>🆕 New booking</b> · {source}\n📅 {day}\n{line}"


async def new_booking_message(appointment: Appointment, db: AsyncSession) -> str | None:
    """Resolve service names and build the message. Returns None on failure.

    Call this inside the request, while the DB session is still open, and send
    the result afterwards (e.g. as a background task).
    """
    try:
        result = await db.execute(
            select(NailType).where(NailType.id == appointment.nail_type_id)
        )
        nail_type = result.scalar_one_or_none()
        nail_type_name = nail_type.name if nail_type else "Nail Service"

        design_tier_name = None
        if appointment.design_tier_id:
            result = await db.execute(
                select(DesignTier).where(DesignTier.id == appointment.design_tier_id)
            )
            design_tier = result.scalar_one_or_none()
            design_tier_name = design_tier.name if design_tier else None

        return build_new_booking_message(appointment, nail_type_name, design_tier_name)
    except Exception as e:  # noqa: BLE001 — never let a notification break a booking
        logger.error("Failed to build new-booking message for %s: %s", appointment.id, e)
        return None


async def notify_new_booking(appointment: Appointment, db: AsyncSession) -> None:
    """Build and send the new-booking ping right away. Never raises."""
    message = await new_booking_message(appointment, db)
    if message:
        await send_message(message)
