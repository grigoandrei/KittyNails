from src.services.service_crud import get_active_services
from src.schemas.service import ServiceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from src.database import get_db

router = APIRouter()

@router.get("/api/services", response_model=list[ServiceResponse])
async def get_active(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await get_active_services(db, skip=skip, limit=limit)