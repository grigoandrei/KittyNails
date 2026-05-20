from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.service import ServiceCreate
from src.models.service import Service
from sqlalchemy import select

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