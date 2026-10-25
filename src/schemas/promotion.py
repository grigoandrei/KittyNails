from datetime import date

from pydantic import BaseModel


class PromotionResponse(BaseModel):
    name: str
    percent: float
    start: date
    end: date
    design_tiers: list[str]
