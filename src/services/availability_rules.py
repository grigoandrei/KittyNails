from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.availability_rule import AvailabilityRulesCreate, AvailabilityRulesUpdate
from src.models.availability_rules import AvailabilityRules
from sqlalchemy import select
from uuid import UUID

async def create_availability_rule(data: AvailabilityRulesCreate, db: AsyncSession) -> AvailabilityRules:

    if data.start_time >= data.end_time:
        raise ValueError("start_time must be before end_time")
    
    if not (0 <= data.day_of_week <= 6):
        raise ValueError("day_of_week must be between 0 and 6")

    availability_rule = AvailabilityRules(
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    db.add(availability_rule)
    await db.commit()
    await db.refresh(availability_rule)
    return availability_rule

async def get_all_availability_rules(db: AsyncSession) -> list[AvailabilityRules]:
    result = await db.execute(select(AvailabilityRules))
    return result.scalars().all()

async def update_availability_rules(rule_id: UUID, data: AvailabilityRulesUpdate, db: AsyncSession) -> AvailabilityRules:
    result = await db.execute(select(AvailabilityRules).where(AvailabilityRules.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise ValueError("Availability rule does not exist!")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(rule, key, value)

    if rule.start_time >= rule.end_time:
        raise ValueError("start_time must be before end_time")

    await db.commit()
    await db.refresh(rule)
    return rule

async def delete_availability_rule(rule_id: UUID, db: AsyncSession):
    result = await db.execute(select(AvailabilityRules).where(AvailabilityRules.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise ValueError("Availability rule does not exist!")

    await db.delete(rule)
    await db.commit()
