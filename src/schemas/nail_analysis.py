from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NailTypeLabel(str, Enum):
    """The fixed vocabulary the AI classifies a photo into. These names must
    match the `name` column of the seeded nail_types rows so the backend can
    look up the current price/duration."""

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


class LengthClassification(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    UNCERTAIN = "uncertain"


class DesignComplexityClassification(str, Enum):
    MINIMAL = "minimal"
    MEDIUM = "medium"
    COMPLEX = "complex"
    UNCERTAIN = "uncertain"


class ExtensionsClassification(str, Enum):
    NATURAL = "natural"
    EXTENSIONS = "extensions"
    UNCERTAIN = "uncertain"


class DesignElements(BaseModel):
    french: bool = False
    chrome: bool = False
    cat_eye: bool = False
    ombre: bool = False
    solid_color: bool = False
    simple_line_art: bool = False
    simple_abstract_art: bool = False
    floral_design: bool = False
    detailed_hand_painted_art: bool = False
    characters_or_illustrations: bool = False
    gems_or_rhinestones: bool = False
    charms: bool = False
    three_d_elements: bool = False
    multiple_colors: bool = False
    different_designs_on_different_nails: bool = False


class NailClassification(BaseModel):
    """Flat structured output for the vision model. Kept simple to avoid
    grammar compilation timeouts on Bedrock structured output."""

    length: LengthClassification
    length_confidence: float = Field(ge=0, le=1)
    design_complexity: DesignComplexityClassification
    design_complexity_confidence: float = Field(ge=0, le=1)
    extensions: ExtensionsClassification
    extensions_confidence: float = Field(ge=0, le=1)
    visible_details: str = Field(max_length=1000)
    uncertainties: str = Field(max_length=1000)


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
    length: str
    design_elements: DesignElements | None = None
