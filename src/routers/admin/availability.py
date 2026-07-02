from src.schemas.availability_rule import AvailabilityRulesCreate, AvailabilityRulesUpdate, AvailabilityRulesResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from uuid import UUID
from src.services.availability_rules import create_availability_rule, update_availability_rules, delete_availability_rule, get_all_availability_rules
from src.auth import get_current_admin

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.post("/api/admin/availability-rules", response_model=AvailabilityRulesResponse, status_code=201)
async def create(data: AvailabilityRulesCreate, db: AsyncSession = Depends(get_db)):
    return await create_availability_rule(data, db)

@router.get("/api/admin/availability-rules", response_model=list[AvailabilityRulesResponse])
async def get_all(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await get_all_availability_rules(db, skip=skip, limit=limit)

@router.put("/api/admin/availability-rules/{rule_id}", response_model=AvailabilityRulesResponse)
async def update(rule_id: UUID, data: AvailabilityRulesUpdate, db: AsyncSession = Depends(get_db)):
    return await update_availability_rules(rule_id, data, db)

@router.delete("/api/admin/availability-rules/{rule_id}", status_code=204)
async def delete(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    await delete_availability_rule(rule_id, db)