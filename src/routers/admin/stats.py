from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_admin
from src.database import get_db
from src.services.income_service import weekly_income

router = APIRouter(prefix="/api/admin/stats", tags=["admin-stats"], dependencies=[Depends(get_current_admin)])


class WeeklyIncome(BaseModel):
    week_start: date
    income: float
    appointments: int


@router.get("/weekly-income", response_model=list[WeeklyIncome])
async def get_weekly_income(
    start: date,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    return await weekly_income(db, start)
