from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.service import ServiceCreate, ServiceUpdate
from src.models.service import Service
from sqlalchemy import select
from uuid import UUID

async def create_service(data: ServiceCreate, db: AsyncSession) -> Service:
    result = await db.execute(select(Service).where(Service.name == data.name))
    existing = result.scalar_one_or_none()

    if existing:
        raise ValueError("Service already exists!")

    service = Service(
        name=data.name,
        duration_minutes=data.duration_minutes,
        price=data.price
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

async def update_service(service_id: UUID, data: ServiceUpdate, db: AsyncSession) -> Service:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()

    if not service:
        raise ValueError("Service does not exist!")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service
