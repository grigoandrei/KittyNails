from datetime import date, datetime

from src.config import settings
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.services.slots_service import BERLIN_TZ


def round_promo_price(price: float) -> float:
    """Snap a discounted price to a whole euro or a half euro. Cents below 50
    round down, above 50 round up, and exactly 50 stay: 55.25 -> 55,
    63.75 -> 64, 42.50 -> 42.50."""
    euros, cents = divmod(round(price * 100), 100)
    if cents < 50:
        return float(euros)
    if cents > 50:
        return float(euros + 1)
    return euros + 0.5


def is_promo_tier(design_tier: DesignTier | None) -> bool:
    return (
        settings.PROMO_PERCENT > 0
        and design_tier is not None
        and design_tier.name in settings.PROMO_DESIGN_TIERS
    )


def is_promo_day(day: date) -> bool:
    return settings.PROMO_START <= day <= settings.PROMO_END


def compute_price(
    nail_type: NailType,
    design_tier: DesignTier | None,
    needs_removal: bool,
    start_time: datetime,
) -> float:
    """Single source of truth for an appointment's price. The promo discount
    applies to the service price only; the removal fee is always full price."""
    price = float(nail_type.price) + (float(design_tier.price) if design_tier else 0)

    if is_promo_tier(design_tier) and is_promo_day(start_time.astimezone(BERLIN_TZ).date()):
        price = round_promo_price(price * (1 - settings.PROMO_PERCENT / 100))

    if needs_removal:
        price += float(settings.NAIL_REMOVAL_PRICE)

    return price
