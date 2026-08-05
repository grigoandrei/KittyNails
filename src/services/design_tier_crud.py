from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.design_tier import DesignTierCreate, DesignTierUpdate
from src.models.design_tier import DesignTier
from sqlalchemy import select
from src.exceptions import NotFoundError, ConflictError
from uuid import UUID

async def create_design_tier(data: DesignTierCreate, db: AsyncSession) -> DesignTier:
    result = await db.execute(select(DesignTier).where(DesignTier.name == data.name))
    existing = result.scalar_one_or_none()

    if existing:
        raise ConflictError("Design tier already exists!")

    design_tier = DesignTier(
        name=data.name,
        duration_minutes=data.duration_minutes,
        price=data.price,
        sort_order=data.sort_order,
    )
    db.add(design_tier)
    await db.commit()
    await db.refresh(design_tier)
    return design_tier

async def update_design_tier(design_tier_id: UUID, data: DesignTierUpdate, db: AsyncSession) -> DesignTier:
    result = await db.execute(select(DesignTier).where(DesignTier.id == design_tier_id))
    design_tier = result.scalar_one_or_none()

    if not design_tier:
        raise NotFoundError("Design tier does not exist!")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(design_tier, key, value)

    await db.commit()
    await db.refresh(design_tier)
    return design_tier

async def get_all_design_tiers(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[DesignTier]:
    result = await db.execute(
        select(DesignTier).order_by(DesignTier.sort_order).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_active_design_tiers(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[DesignTier]:
    result = await db.execute(
        select(DesignTier).where(DesignTier.is_active).order_by(DesignTier.sort_order).offset(skip).limit(limit)
    )
    return result.scalars().all()
