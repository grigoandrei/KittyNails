from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.nail_type import NailTypeCreate, NailTypeUpdate
from src.models.nail_type import NailType
from sqlalchemy import select
from src.exceptions import NotFoundError, ConflictError
from uuid import UUID

async def create_nail_type(data: NailTypeCreate, db: AsyncSession) -> NailType:
    result = await db.execute(select(NailType).where(NailType.name == data.name))
    existing = result.scalar_one_or_none()

    if existing:
        raise ConflictError("Nail type already exists!")

    nail_type = NailType(
        name=data.name,
        duration_minutes=data.duration_minutes,
        price=data.price,
        sort_order=data.sort_order,
    )
    db.add(nail_type)
    await db.commit()
    await db.refresh(nail_type)
    return nail_type

async def update_nail_type(nail_type_id: UUID, data: NailTypeUpdate, db: AsyncSession) -> NailType:
    result = await db.execute(select(NailType).where(NailType.id == nail_type_id))
    nail_type = result.scalar_one_or_none()

    if not nail_type:
        raise NotFoundError("Nail type does not exist!")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(nail_type, key, value)

    await db.commit()
    await db.refresh(nail_type)
    return nail_type

async def get_all_nail_types(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[NailType]:
    result = await db.execute(
        select(NailType).order_by(NailType.sort_order).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_active_nail_types(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[NailType]:
    result = await db.execute(
        select(NailType).where(NailType.is_active).order_by(NailType.sort_order).offset(skip).limit(limit)
    )
    return result.scalars().all()
