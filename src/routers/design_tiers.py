from src.services.design_tier_crud import get_active_design_tiers
from src.schemas.design_tier import DesignTierResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.database import get_db

router = APIRouter()

@router.get("/api/design-tiers", response_model=list[DesignTierResponse])
async def get_active(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_active_design_tiers(db, skip=skip, limit=limit)
