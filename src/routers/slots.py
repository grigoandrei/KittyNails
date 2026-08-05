from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.slots_service import get_available_slots, get_available_dates
from datetime import date, datetime
from uuid import UUID

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("/", response_model=list[datetime])
async def available_slots(
    nail_type_id: UUID,
    design_tier_id: UUID,
    target_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    return await get_available_slots(db, nail_type_id, design_tier_id, target_date)


@router.get("/dates", response_model=list[date])
async def available_dates(
    nail_type_id: UUID,
    design_tier_id: UUID,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
):
    return await get_available_dates(db, nail_type_id, design_tier_id, year, month)
