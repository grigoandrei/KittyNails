"""Daily Telegram overview of the current day's appointments.

Intended to run once a day at 08:00 Europe/Berlin (via a dedicated scheduler
container). Queries today's (Berlin day) BOOKED appointments and sends the
artist a formatted Telegram message.
"""

import asyncio
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config import settings
from src.models.appointment import Appointment, Status
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.services.telegram_service import format_appointment_line, send_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _today_berlin_bounds(now: datetime) -> tuple[datetime, datetime, date]:
    """Return (start, end, date) for today in Berlin, as tz-aware datetimes.

    start is 00:00 today Berlin, end is 00:00 tomorrow — a half-open
    [start, end) range that the DB can compare against tz-aware start_time.
    """
    today = now.astimezone(BERLIN_TZ).date()
    start = datetime.combine(today, time.min, tzinfo=BERLIN_TZ)
    end = start + timedelta(days=1)
    return start, end, today


def build_digest_message(appointments: list[dict], target_date) -> str:
    """Build the digest text from pre-resolved appointment dicts.

    Each dict: start_time, nail_type_name, design_tier_name, needs_removal,
    quoted_price, client_email. Pure function — no DB — so it's easy to test.
    """
    header = f"<b>📅 Today's appointments · {target_date.strftime('%A, %B %d')}</b>"
    if not appointments:
        return f"{header}\n\nNo appointments today. 💅"

    lines = [
        format_appointment_line(
            a["start_time"],
            a["nail_type_name"],
            a["design_tier_name"],
            a["needs_removal"],
            a["quoted_price"],
            a["client_email"],
        )
        for a in appointments
    ]
    count = len(appointments)
    plural = "s" if count != 1 else ""
    return f"{header}\n<i>{count} appointment{plural}</i>\n\n" + "\n\n".join(lines)


async def _send_digest():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with async_session() as db:
            start, end, target_date = _today_berlin_bounds(datetime.now(BERLIN_TZ))

            query = (
                select(Appointment)
                .where(
                    Appointment.status == Status.BOOKED,
                    Appointment.start_time >= start,
                    Appointment.start_time < end,
                )
                .order_by(Appointment.start_time)
            )
            result = await db.execute(query)
            appointments = result.scalars().all()

            resolved = []
            for appt in appointments:
                nt = await db.execute(
                    select(NailType).where(NailType.id == appt.nail_type_id)
                )
                nail_type = nt.scalar_one_or_none()
                design_tier_name = None
                if appt.design_tier_id:
                    dt = await db.execute(
                        select(DesignTier).where(DesignTier.id == appt.design_tier_id)
                    )
                    design_tier = dt.scalar_one_or_none()
                    if design_tier:
                        design_tier_name = design_tier.name
                resolved.append(
                    {
                        "start_time": appt.start_time,
                        "nail_type_name": nail_type.name if nail_type else "Nail Service",
                        "design_tier_name": design_tier_name,
                        "needs_removal": appt.needs_removal,
                        "quoted_price": float(appt.quoted_price),
                        "client_email": appt.client_email,
                    }
                )

            message = build_digest_message(resolved, target_date)
            sent = await send_message(message)
            logger.info(
                "Digest for %s: %d appointments, sent=%s",
                target_date.isoformat(),
                len(resolved),
                sent,
            )
            return {"date": target_date.isoformat(), "count": len(resolved), "sent": sent}
    finally:
        await engine.dispose()


def handler(event, context):
    """Entry point for the daily digest job."""
    result = asyncio.run(_send_digest())
    return {"statusCode": 200, "body": result}


# Hour of day (Europe/Berlin) at which the digest runs.
DIGEST_HOUR = 8


def seconds_until_next_run(now: datetime, hour: int = DIGEST_HOUR) -> float:
    """Seconds from `now` until the next `hour`:00 Europe/Berlin.

    DST-safe: computes the target wall-clock time in Berlin and lets zoneinfo
    resolve the offset, rather than assuming a fixed UTC offset. Always returns
    a positive value (rolls to tomorrow if today's time has passed).
    """
    berlin_now = now.astimezone(BERLIN_TZ)
    target = berlin_now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= berlin_now:
        target = target + timedelta(days=1)
    return (target - berlin_now).total_seconds()


def run_forever():
    """Loop: sleep until the next 08:00 Berlin, send the digest, repeat."""
    import time as _time

    while True:
        sleep_seconds = seconds_until_next_run(datetime.now(BERLIN_TZ))
        logger.info("Digest scheduler sleeping %.0fs until next run", sleep_seconds)
        _time.sleep(sleep_seconds)
        try:
            handler({}, None)
        except Exception as e:  # noqa: BLE001 — keep the scheduler alive
            logger.error("Digest run failed: %s", e)
        # Small guard sleep so we don't re-fire within the same minute.
        _time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_forever()
