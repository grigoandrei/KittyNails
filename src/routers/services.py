from src.services.service_crud import get_active_services
from src.schemas.service import ServiceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from src.database import get_db

router = APIRouter()

@router.get("/api/services", response_model=list[ServiceResponse])
async def get_active(db: AsyncSession = Depends(get_db)):
    result = await get_active_services(db)
    return result