from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.slots_service import get_available_dates, get_available_slots

router = APIRouter(prefix="/api/slots", tags=["slots"])


def _require_one_service(nail_type_id: UUID | None, monthly_set_model_id: UUID | None):
    if (nail_type_id is None) == (monthly_set_model_id is None):
        raise HTTPException(
            status_code=422,
            detail="Pass exactly one of nail_type_id or monthly_set_model_id.",
        )


@router.get("/", response_model=list[datetime])
async def available_slots(
    target_date: date = Query(..., alias="date"),
    nail_type_id: UUID | None = None,
    design_tier_id: UUID | None = None,
    monthly_set_model_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    _require_one_service(nail_type_id, monthly_set_model_id)
    return await get_available_slots(
        db, nail_type_id, design_tier_id, target_date, monthly_set_model_id
    )


@router.get("/dates", response_model=list[date])
async def available_dates(
    year: int,
    month: int,
    nail_type_id: UUID | None = None,
    design_tier_id: UUID | None = None,
    monthly_set_model_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    _require_one_service(nail_type_id, monthly_set_model_id)
    return await get_available_dates(
        db, nail_type_id, design_tier_id, year, month, monthly_set_model_id
    )
