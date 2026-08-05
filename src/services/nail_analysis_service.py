import base64
from functools import lru_cache

from anthropic import AnthropicBedrock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import NotFoundError, ValidationError
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.schemas.nail_analysis import NailAnalysisResponse, NailClassification

# The image formats we accept from clients. Maps a detected/declared content
# type to the media_type Bedrock expects.
SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

MAX_REASONING_LENGTH = 1000

SYSTEM_PROMPT = (
    "You are a nail-salon assistant. You are shown a photo of a client's desired "
    "nails. Classify the photo into exactly one nail type and one design tier from "
    "the fixed categories provided by the response schema.\n\n"
    "Nail types describe length/structure:\n"
    "- Short: natural-length nails, minimal or no extension.\n"
    "- Regular: medium length, standard manicure length.\n"
    "- Extensions: clearly extended nails (gel/acrylic tips well past the fingertip).\n\n"
    "Design tiers describe artwork complexity:\n"
    "- Simple: single colour, French, or minimal accent.\n"
    "- Medium: a few accent nails, simple patterns, glitter, or gradients.\n"
    "- Advanced: intricate hand-painted art, 3D elements, detailed multi-nail designs.\n\n"
    "You ONLY classify. Never mention or invent a price or a duration. "
    "Set confidence to 'low' if the photo is blurry, not of nails, or ambiguous. "
    "Keep the reasoning to one or two short sentences."
)


@lru_cache(maxsize=1)
def get_client() -> AnthropicBedrock:
    """Bedrock client. Auth comes from the default AWS credential chain (IAM
    role in Lambda); region is pinned to settings.AWS_REGION so we never depend
    on an ambient AWS_REGION. Cached so we reuse one client across requests."""
    return AnthropicBedrock(aws_region=settings.AWS_REGION)


def _classify_image(image_bytes: bytes, media_type: str) -> NailClassification:
    """Single Bedrock call that returns the structured classification. Kept
    synchronous and free of DB access so it is trivial to mock in tests."""
    if media_type not in SUPPORTED_MEDIA_TYPES:
        raise ValidationError(f"Unsupported image type: {media_type}")

    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")

    message = get_client().messages.parse(
        model=settings.NAIL_ANALYSIS_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_format=NailClassification,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Classify these nails.",
                    },
                ],
            }
        ],
    )

    if message.stop_reason == "refusal":
        raise ValidationError(
            "The image could not be analyzed. Please upload a clear photo of nails."
        )

    classification = message.parsed_output
    if classification is None:
        raise ValidationError("Could not classify the uploaded image. Please try another photo.")

    return classification


async def analyze_nails(
    image_bytes: bytes,
    media_type: str,
    db: AsyncSession,
) -> NailAnalysisResponse:
    """Classify a nail photo, then price it server-side from the active DB rows.
    The AI never sees or produces prices — it only picks the two labels."""
    classification = _classify_image(image_bytes, media_type)

    result = await db.execute(
        select(NailType).where(
            NailType.name == classification.nail_type.value,
            NailType.is_active,
        )
    )
    nail_type = result.scalar_one_or_none()

    result = await db.execute(
        select(DesignTier).where(
            DesignTier.name == classification.design_tier.value,
            DesignTier.is_active,
        )
    )
    design_tier = result.scalar_one_or_none()

    # The AI returned a valid label, but the salon may have deactivated that
    # category. Surface it rather than silently mispricing.
    if not nail_type or not design_tier:
        raise NotFoundError(
            "The classified nail category is not currently offered. Please contact the salon."
        )

    estimated_price = float(nail_type.price) + float(design_tier.price)
    estimated_duration = nail_type.duration_minutes + design_tier.duration_minutes
    reasoning = classification.reasoning[:MAX_REASONING_LENGTH]

    return NailAnalysisResponse(
        nail_type_id=nail_type.id,
        design_tier_id=design_tier.id,
        nail_type=nail_type.name,
        design_tier=design_tier.name,
        estimated_price=estimated_price,
        estimated_duration_minutes=estimated_duration,
        confidence=classification.confidence.value,
        reasoning=reasoning,
    )
