from datetime import datetime

from fastapi import APIRouter

from src.config import settings
from src.schemas.promotion import PromotionResponse
from src.services.slots_service import BERLIN_TZ

router = APIRouter()


@router.get("/api/promotion", response_model=PromotionResponse | None)
async def get_promotion():
    """The current promo, for display only. The backend applies it at booking.
    Returns null when the promo is off or its window has passed."""
    if settings.PROMO_PERCENT <= 0 or settings.PROMO_END < datetime.now(BERLIN_TZ).date():
        return None
    return PromotionResponse(
        name=settings.PROMO_NAME,
        percent=settings.PROMO_PERCENT,
        start=settings.PROMO_START,
        end=settings.PROMO_END,
        design_tiers=settings.PROMO_DESIGN_TIERS,
    )
