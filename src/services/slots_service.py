from datetime import date, datetime, timedelta, time, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.service import Service
from src.models.availability_rules import AvailabilityRules
from src.models.blocked_time import BlockedTime
from src.models.appointment import Appointment, Status


async def get_available_slots(
    db: AsyncSession,
    service_id: UUID,
    target_date: date,
) -> list[datetime]:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise ValueError("Service not found!")

    duration = timedelta(minutes=service.duration_minutes)

    day_of_week = target_date.weekday()
    result = await db.execute(
        select(AvailabilityRules).where(AvailabilityRules.day_of_week == day_of_week)
    )
    rules = result.scalars().all()
    if not rules:
        return []

    day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

    result = await db.execute(
        select(Appointment).where(
            Appointment.status == Status.BOOKED,
            Appointment.start_time >= day_start,
            Appointment.start_time <= day_end,
        )
    )
    booked = result.scalars().all()

    result = await db.execute(
        select(BlockedTime).where(
            BlockedTime.start_time < day_end,
            BlockedTime.end_time > day_start,
        )
    )
    blocked = result.scalars().all()

    available = []
    for rule in rules:
        slot_start_time = rule.start_time
        while True:
            slot_start = datetime.combine(target_date, slot_start_time, tzinfo=timezone.utc)
            slot_end = slot_start + duration

            if slot_end.time() > rule.end_time:
                break

            has_conflict = any(
                slot_start < appt.end_time and slot_end > appt.start_time
                for appt in booked
            )

            is_blocked = any(
                slot_start < bt.end_time and slot_end > bt.start_time
                for bt in blocked
            )

            if not has_conflict and not is_blocked:
                available.append(slot_start)

            slot_start_time = (slot_start + duration).time()

    return sorted(available)


async def get_available_dates(
    db: AsyncSession,
    service_id: UUID,
    year: int,
    month: int,
) -> list[date]:
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    available_dates = []
    current = first_day
    today = date.today()

    while current <= last_day:
        if current >= today:
            slots = await get_available_slots(db, service_id, current)
            if slots:
                available_dates.append(current)
        current += timedelta(days=1)

    return available_dates
