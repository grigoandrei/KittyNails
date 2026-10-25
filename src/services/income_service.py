from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.appointment import Appointment, Status
from src.services.slots_service import BERLIN_TZ

# Appointments that brought in money. BOOKED is included because the artist
# doesn't always mark past appointments COMPLETED.
EARNING_STATUSES = (Status.BOOKED, Status.COMPLETED)


def week_start(d: date) -> date:
    """Monday of the week containing `d`."""
    return d - timedelta(days=d.weekday())


async def weekly_income(
    db: AsyncSession, start: date, now: datetime | None = None
) -> list[dict]:
    """Income per Berlin-local Monday-start week, from `start`'s week to now.

    Only appointments that already started count. Weeks with no income are
    included with 0 so the chart has no gaps.
    """
    now = now or datetime.now(UTC)
    first_week = week_start(start)
    last_week = week_start(now.astimezone(BERLIN_TZ).date())
    range_start = datetime.combine(start, time.min, tzinfo=BERLIN_TZ)

    result = await db.execute(
        select(Appointment.start_time, Appointment.quoted_price).where(
            and_(
                Appointment.status.in_(EARNING_STATUSES),
                Appointment.start_time >= range_start,
                Appointment.start_time <= now,
            )
        )
    )

    weeks: dict[date, dict] = {}
    week = first_week
    while week <= last_week:
        weeks[week] = {"week_start": week, "income": 0.0, "appointments": 0}
        week += timedelta(days=7)

    for start_time, price in result.all():
        bucket = weeks.get(week_start(start_time.astimezone(BERLIN_TZ).date()))
        if bucket:
            bucket["income"] += float(price)
            bucket["appointments"] += 1

    return list(weeks.values())
