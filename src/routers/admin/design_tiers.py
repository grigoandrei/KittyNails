from src.schemas.design_tier import DesignTierCreate, DesignTierResponse, DesignTierUpdate
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.design_tier_crud import create_design_tier, update_design_tier, get_all_design_tiers
from src.auth import get_current_admin
from uuid import UUID

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.post("/api/admin/design-tiers", response_model=DesignTierResponse, status_code=201)
async def create(data: DesignTierCreate, db: AsyncSession = Depends(get_db)):
    return await create_design_tier(data, db)

@router.put("/api/admin/design-tiers/{design_tier_id}", response_model=DesignTierResponse)
async def update(design_tier_id: UUID, data: DesignTierUpdate, db: AsyncSession = Depends(get_db)):
    return await update_design_tier(design_tier_id, data, db)

@router.get("/api/admin/design-tiers", response_model=list[DesignTierResponse])
async def get_design_tiers(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_all_design_tiers(db, skip=skip, limit=limit)
