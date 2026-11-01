from src.config import settings
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType


def compute_price(
    nail_type: NailType,
    design_tier: DesignTier | None,
    needs_removal: bool,
) -> float:
    """Single source of truth for an appointment's price."""
    price = float(nail_type.price) + (float(design_tier.price) if design_tier else 0)

    if needs_removal:
        price += float(settings.NAIL_REMOVAL_PRICE)

    return price
