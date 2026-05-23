from src.schemas.availability_rule import AvailabilityRulesCreate, AvailabilityRulesUpdate, AvailabilityRulesResponse
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from uuid import UUID
from src.services.availability_rules import create_availability_rule, update_availability_rules, delete_availability_rule, get_all_availability_rules

router = APIRouter()

@router.post("/api/admin/availability-rules", response_model=AvailabilityRulesResponse,status_code=201)
async def create(data: AvailabilityRulesCreate, db: AsyncSession = Depends(get_db)):
    try:
        rule = await create_availability_rule(data, db)
    except ValueError as e:
        if "before" in str(e) or "between" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    return rule

@router.get("/api/admin/availability-rules", response_model=list[AvailabilityRulesResponse], status_code=200)
async def get_all(db: AsyncSession = Depends(get_db)):
    result = await get_all_availability_rules(db)
    return result

@router.put("/api/admin/availability-rules/{rule_id}", response_model=AvailabilityRulesResponse, status_code=200)
async def update(rule_id: UUID, data: AvailabilityRulesUpdate, db: AsyncSession = Depends(get_db)):
    try:
        rule = await update_availability_rules(rule_id, data, db)
    except ValueError as e:
        if "not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))

    return rule

@router.delete("/api/admin/availability-rules/{rule_id}", status_code=204)
async def delete(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await delete_availability_rule(rule_id, db)
    except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))