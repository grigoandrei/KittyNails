"""Lambda handler for sending appointment reminder emails.

Triggered by EventBridge Scheduler (e.g. every hour), this queries for
appointments that are approximately 24 hours away and sends reminder emails.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import settings
from src.models.appointment import Appointment, Status
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.services.email_service import send_reminder_email

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def _send_reminders():
    """Find appointments ~24h away and send reminder emails."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as db:
            # Find appointments starting between 23 and 25 hours from now.
            # This 2-hour window ensures we don't miss any if the scheduler
            # runs slightly off-schedule (and avoids double-sending with a
            # 1-hour trigger interval).
            now = datetime.now(UTC)
            window_start = now + timedelta(hours=23)
            window_end = now + timedelta(hours=25)

            query = select(Appointment).where(
                Appointment.status == Status.BOOKED,
                Appointment.start_time >= window_start,
                Appointment.start_time < window_end,
            )
            result = await db.execute(query)
            appointments = result.scalars().all()

            logger.info(
                "Found %d appointments in reminder window (%s to %s)",
                len(appointments),
                window_start.isoformat(),
                window_end.isoformat(),
            )

            sent_count = 0
            for appt in appointments:
                # Look up service names
                nail_type_name = "Nail Service"
                nt_result = await db.execute(
                    select(NailType).where(NailType.id == appt.nail_type_id)
                )
                nail_type = nt_result.scalar_one_or_none()
                if nail_type:
                    nail_type_name = nail_type.name

                design_tier_name = None
                if appt.design_tier_id:
                    dt_result = await db.execute(
                        select(DesignTier).where(DesignTier.id == appt.design_tier_id)
                    )
                    design_tier = dt_result.scalar_one_or_none()
                    if design_tier:
                        design_tier_name = design_tier.name

                success = await send_reminder_email(
                    client_email=appt.client_email,
                    start_time=appt.start_time,
                    nail_type_name=nail_type_name,
                    design_tier_name=design_tier_name,
                )
                if success:
                    sent_count += 1

            logger.info(
                "Sent %d reminder emails out of %d appointments",
                sent_count,
                len(appointments),
            )
            return {
                "reminders_sent": sent_count,
                "appointments_found": len(appointments),
            }
    finally:
        await engine.dispose()


def handler(event, context):
    """Lambda entry point for the reminder email scheduler."""
    result = asyncio.run(_send_reminders())
    return {
        "statusCode": 200,
        "body": result,
    }
