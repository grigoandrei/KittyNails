from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.appointment import AppointmentCreate
from src.models.appointment import Appointment
from sqlalchemy import select
from src.models.service import Service
from datetime import timedelta
from src.models.appointment import Status

async def create_appointment(data: AppointmentCreate, db: AsyncSession) -> Appointment:
    result = await db.execute(select(Service).where(Service.id == data.service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise ValueError("Service not found!")

    end_time = data.start_time + timedelta(minutes=service.duration_minutes)

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