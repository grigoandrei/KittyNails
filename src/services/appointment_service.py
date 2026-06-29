from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.appointment import AppointmentCreate
from src.models.appointment import Appointment
from sqlalchemy import select
from src.models.service import Service
from src.models.availability_rules import AvailabilityRules
from src.models.blocked_time import BlockedTime
from datetime import timedelta
from src.models.appointment import Status

async def create_appointment(data: AppointmentCreate, db: AsyncSession) -> Appointment:
    result = await db.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise ValueError("Service not found!")

    end_time = data.start_time + timedelta(minutes=service.duration_minutes)

    day_of_week = data.start_time.weekday()
    availability_query = select(AvailabilityRules).where(AvailabilityRules.day_of_week == day_of_week)
    result = await db.execute(availability_query)
    rules = result.scalars().all()

    if not rules:
        raise ValueError("Salon is closed on this day!")

    appointment_start = data.start_time.time()
    appointment_end = end_time.time()

    is_within_hours = any(
        rule.start_time <= appointment_start and rule.end_time >= appointment_end
        for rule in rules
    )

    if not is_within_hours:
        raise ValueError("Appointment is outside salon working hours!")

    blocked_query = select(BlockedTime).where(
        BlockedTime.start_time < end_time,
        BlockedTime.end_time > data.start_time
    )

    result = await db.execute(blocked_query)
    blocked = result.scalars().first()

    if blocked:
        raise ValueError("This time slot is blocked!")

    conflict_query = select(Appointment).where(
        Appointment.status == Status.BOOKED,
        Appointment.start_time < end_time,
        Appointment.end_time > data.start_time,
    )
    result = await db.execute(conflict_query)
    conflict = result.scalars().first()

    if conflict:
        raise ValueError("Time slot is already booked!")

    appointment = Appointment(
        service_id=data.service_id,
        client_email=data.client_email,
        start_time=data.start_time,
        end_time=end_time,
        status=Status.BOOKED,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment