from src.services.nail_type_crud import get_active_nail_types
from src.schemas.nail_type import NailTypeResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.database import get_db

router = APIRouter()

@router.get("/api/nail-types", response_model=list[NailTypeResponse])
async def get_active(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_active_nail_types(db, skip=skip, limit=limit)
