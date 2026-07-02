from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.blocked_time import BlockedTimeCreate
from src.models.blocked_time import BlockedTime
from sqlalchemy import select
from src.exceptions import NotFoundError, ConflictError, ValidationError
from uuid import UUID

async def create_blocked_time(data: BlockedTimeCreate, db: AsyncSession) -> BlockedTime:
    if data.start_time >= data.end_time:
        raise ValidationError("start_time must be before end_time")

    existing = await db.execute(
        select(BlockedTime).where(
            BlockedTime.start_time == data.start_time,
            BlockedTime.end_time == data.end_time
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("This time range is already blocked")

    blocked_time = BlockedTime(
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason
    )

    db.add(blocked_time)
    await db.commit()
    await db.refresh(blocked_time)
    return blocked_time

async def get_blocked_times(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[BlockedTime]:
    result = await db.execute(select(BlockedTime).offset(skip).limit(limit))
    return result.scalars().all()

async def delete_blocked_time(time_id: UUID, db: AsyncSession):
    result = await db.execute(select(BlockedTime).where(BlockedTime.id == time_id))
    time = result.scalar_one_or_none()

    if not time:
        raise NotFoundError("Blocked time does not exist!")

    await db.delete(time)
    await db.commit()