from src.schemas.blocked_time import BlockedTimeCreate, BlockedTimeResponse
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from uuid import UUID
from src.services.blocked_time_service import create_blocked_time, delete_blocked_time, get_blocked_times

router = APIRouter()

@router.post("/api/admin/blocked-times", response_model=BlockedTimeResponse, status_code=201)
async def create(data: BlockedTimeCreate, db: AsyncSession = Depends(get_db)):
    try:
        time = await create_blocked_time(data, db)
    except ValueError as e:
        if "before" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=409, detail=str(e))
    return time

@router.get("/api/admin/blocked-times", response_model=list[BlockedTimeResponse], status_code=200)
async def get_all(db: AsyncSession = Depends(get_db)):
    result = await get_blocked_times(db)
    return result

@router.delete("/api/admin/blocked-times/{time_id}", status_code=204)
async def delete(time_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        await delete_blocked_time(time_id, db)
    except ValueError as e:
         raise HTTPException(status_code=404, detail=str(e))