from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NailTypeLabel(str, Enum):
    """The fixed vocabulary the AI classifies a photo into. These names must
    match the `name` column of the seeded nail_types rows so the backend can
    look up the current price/duration."""
    SHORT = "Short"
    REGULAR = "Regular"
    EXTENSIONS = "Extensions"


class DesignTierLabel(str, Enum):
    """Fixed vocabulary for design complexity; must match design_tiers.name."""
    SIMPLE = "Simple"
    MEDIUM = "Medium"
    ADVANCED = "Advanced"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NailClassification(BaseModel):
    """Structured output the vision model is forced to return. The model ONLY
    classifies — it never computes price or duration. The backend derives those
    from the DB rows matching these labels."""
    nail_type: NailTypeLabel
    design_tier: DesignTierLabel
    confidence: Confidence
    reasoning: str = Field(
        max_length=1000,
        description="Brief explanation of why the photo fits these categories.",
    )


class NailAnalysisResponse(BaseModel):
    """What the API returns to the client after classification. Price and
    duration are the server-side estimate; the client sees them as an estimate,
    never a binding quote."""
    model_config = ConfigDict(from_attributes=True)

    nail_type_id: UUID
    design_tier_id: UUID
    nail_type: str
    design_tier: str
    estimated_price: float
    estimated_duration_minutes: int
    confidence: str
    reasoning: str
