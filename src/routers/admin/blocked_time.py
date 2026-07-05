from src.schemas.blocked_time import BlockedTimeCreate, BlockedTimeResponse
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from uuid import UUID
from src.services.blocked_time_service import create_blocked_time, delete_blocked_time, get_blocked_times
from src.auth import get_current_admin

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.post("/api/admin/blocked-times", response_model=BlockedTimeResponse, status_code=201)
async def create(data: BlockedTimeCreate, db: AsyncSession = Depends(get_db)):
    return await create_blocked_time(data, db)

@router.get("/api/admin/blocked-times", response_model=list[BlockedTimeResponse])
async def get_all(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_blocked_times(db, skip=skip, limit=limit)

@router.delete("/api/admin/blocked-times/{time_id}", status_code=204)
async def delete(time_id: UUID, db: AsyncSession = Depends(get_db)):
    await delete_blocked_time(time_id, db)