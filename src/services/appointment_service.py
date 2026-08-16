from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.models.appointment import Appointment, Status
from src.models.availability_rules import AvailabilityRules
from src.models.blocked_time import BlockedTime
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.schemas.appointment import AppointmentCreate


async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession,
    status: Status = Status.BOOKED,
) -> Appointment:
    result = await db.execute(select(NailType).where(NailType.id == data.nail_type_id))
    nail_type = result.scalar_one_or_none()

    if not nail_type or not nail_type.is_active:
        raise NotFoundError("Nail type not available!")

    # Design tier is optional (e.g. Japanese Manicure doesn't use one)
    design_tier = None
    if data.design_tier_id:
        result = await db.execute(
            select(DesignTier).where(DesignTier.id == data.design_tier_id)
        )
        design_tier = result.scalar_one_or_none()

        if not design_tier or not design_tier.is_active:
            raise NotFoundError("Design tier not available!")

    # Duration and price are always derived server-side from the current DB rows
    # so the client can never dictate what they pay.
    total_minutes = nail_type.duration_minutes + (
        design_tier.duration_minutes if design_tier else 0
    )
    quoted_price = float(nail_type.price) + (
        float(design_tier.price) if design_tier else 0
    )

    end_time = data.start_time + timedelta(minutes=total_minutes)

    day_of_week = data.start_time.weekday()
    availability_query = select(AvailabilityRules).where(
        AvailabilityRules.day_of_week == day_of_week
    )
    result = await db.execute(availability_query)
    rules = result.scalars().all()

    if not rules:
        raise ValidationError("Salon is closed on this day!")

    appointment_start = data.start_time.time()
    appointment_end = end_time.time()

    is_within_hours = any(
        rule.start_time <= appointment_start and rule.end_time >= appointment_end
        for rule in rules
    )

    if not is_within_hours:
        raise ValidationError("Appointment is outside salon working hours!")

    blocked_query = select(BlockedTime).where(
        BlockedTime.start_time < end_time, BlockedTime.end_time > data.start_time
    )

    result = await db.execute(blocked_query)
    blocked = result.scalars().first()

    if blocked:
        raise ConflictError("This time slot is blocked!")

    # Check conflicts with both BOOKED and PENDING_PAYMENT appointments
    conflict_query = select(Appointment).where(
        Appointment.status.in_([Status.BOOKED, Status.PENDING_PAYMENT]),
        Appointment.start_time < end_time,
        Appointment.end_time > data.start_time,
    )
    result = await db.execute(conflict_query)
    conflict = result.scalars().first()

    if conflict:
        raise ConflictError("Time slot is already booked!")

    appointment = Appointment(
        nail_type_id=data.nail_type_id,
        design_tier_id=data.design_tier_id,
        client_email=data.client_email,
        start_time=data.start_time,
        end_time=end_time,
        status=status,
        quoted_price=quoted_price,
        ai_confidence=data.ai_confidence,
        ai_reasoning=data.ai_reasoning,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


async def list_appointments(
    db: AsyncSession,
    status: Status | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Appointment]:
    query = select(Appointment)

    filters = []

    if status:
        filters.append(Appointment.status == status)
    if date_from:
        filters.append(Appointment.start_time >= date_from)
    if date_to:
        filters.append(Appointment.end_time < date_to + timedelta(days=1))

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Appointment.start_time.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_appointment_status(
    db: AsyncSession,
    appointment_id: UUID,
    new_status: Status,
) -> Appointment:
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise NotFoundError("Appointment not found!")

    appointment.status = new_status
    await db.commit()
    await db.refresh(appointment)
    return appointment
