from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.appointment import Appointment, Status
from src.models.availability_rules import AvailabilityRules
from src.models.blocked_time import BlockedTime
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType

BERLIN_TZ = ZoneInfo("Europe/Berlin")


async def _resolve_duration(
    db: AsyncSession,
    nail_type_id: UUID,
    design_tier_id: UUID | None,
) -> int:
    """Total appointment length is the nail type plus the design tier (if any).
    For nail types like Japanese Manicure, no design tier is needed."""
    result = await db.execute(select(NailType).where(NailType.id == nail_type_id))
    nail_type = result.scalar_one_or_none()
    if not nail_type or not nail_type.is_active:
        raise NotFoundError("Nail type not available!")

    if design_tier_id is None:
        return nail_type.duration_minutes

    result = await db.execute(select(DesignTier).where(DesignTier.id == design_tier_id))
    design_tier = result.scalar_one_or_none()
    if not design_tier or not design_tier.is_active:
        raise NotFoundError("Design tier not available!")

    return nail_type.duration_minutes + design_tier.duration_minutes


async def get_available_slots(
    db: AsyncSession,
    nail_type_id: UUID,
    design_tier_id: UUID | None,
    target_date: date,
) -> list[datetime]:
    total_minutes = await _resolve_duration(db, nail_type_id, design_tier_id)
    duration = timedelta(minutes=total_minutes)

    day_of_week = target_date.weekday()
    result = await db.execute(
        select(AvailabilityRules).where(AvailabilityRules.day_of_week == day_of_week)
    )
    rules = result.scalars().all()
    if not rules:
        return []

    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)

    result = await db.execute(
        select(Appointment).where(
            Appointment.status.in_([Status.BOOKED, Status.PENDING_PAYMENT]),
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

    def to_naive(dt: datetime) -> datetime:
        """Convert a timezone-aware datetime to naive local time for comparison
        with the naive slot times we generate."""
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(None).replace(tzinfo=None)

    now = datetime.now(BERLIN_TZ).replace(tzinfo=None)

    available = []
    for rule in rules:
        slot_start_time = rule.start_time
        while True:
            slot_start = datetime.combine(target_date, slot_start_time)
            slot_end = slot_start + duration

            if slot_end.time() > rule.end_time:
                break

            # Skip slots that are in the past
            if slot_start <= now:
                slot_start_time = (slot_start + duration).time()
                continue

            has_conflict = any(
                slot_start < to_naive(appt.end_time) and slot_end > to_naive(appt.start_time)
                for appt in booked
            )

            is_blocked = any(
                slot_start < to_naive(bt.end_time) and slot_end > to_naive(bt.start_time)
                for bt in blocked
            )

            if not has_conflict and not is_blocked:
                available.append(slot_start.replace(tzinfo=BERLIN_TZ))

            slot_start_time = (slot_start + duration).time()

    return sorted(available)


async def get_available_dates(
    db: AsyncSession,
    nail_type_id: UUID,
    design_tier_id: UUID | None,
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
            slots = await get_available_slots(db, nail_type_id, design_tier_id, current)
            if slots:
                available_dates.append(current)
        current += timedelta(days=1)

    return available_dates
