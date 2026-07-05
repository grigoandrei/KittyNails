from src.services.service_crud import get_active_services
from src.schemas.service import ServiceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.database import get_db

router = APIRouter()

@router.get("/api/services", response_model=list[ServiceResponse])
async def get_active(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_active_services(db, skip=skip, limit=limit)