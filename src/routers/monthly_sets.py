from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.monthly_set import MonthlySetPublicResponse
from src.services.monthly_set_service import list_available

router = APIRouter(tags=["monthly-sets"])


@router.get("/api/monthly-sets", response_model=list[MonthlySetPublicResponse])
async def available_designs(db: AsyncSession = Depends(get_db)):
    """Designs a client can book right now. Taken and hidden ones are left out."""
    return await list_available(db)
