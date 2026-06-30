from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.slots_service import get_available_slots, get_available_dates
from datetime import date, datetime
from uuid import UUID

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.get("/", response_model=list[datetime])
async def available_slots(
    service_id: UUID,
    target_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_available_slots(db, service_id, target_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dates", response_model=list[date])
async def available_dates(
    service_id: UUID,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_available_dates(db, service_id, year, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
