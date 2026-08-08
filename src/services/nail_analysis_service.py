import base64
from functools import lru_cache

from anthropic import AnthropicBedrock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.exceptions import NotFoundError, ValidationError
from src.models.design_tier import DesignTier
from src.models.nail_type import NailType
from src.schemas.nail_analysis import (
    DesignComplexityClassification,
    ExtensionsClassification,
    NailAnalysisResponse,
    NailClassification,
)

# The image formats we accept from clients. Maps a detected/declared content
# type to the media_type Bedrock expects.
SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

MAX_REASONING_LENGTH = 500

SYSTEM_PROMPT = """\
You are an AI nail design analysis assistant for a professional nail technician.

Your task is to analyze a client's nail inspiration photo and classify the nail design \
based on **length, design complexity, and visible techniques/elements**.

Do NOT estimate the price yourself. Do NOT make assumptions about the nail technician's \
pricing. Your job is only to analyze and classify the design.

## 1. NAIL LENGTH

Classify the visible nail length into one of these categories:

### SHORT
* Nails extend only slightly beyond the fingertip or are approximately at fingertip level.
* The overall appearance is short and practical.
* Do not classify a nail as medium just because the nail plate itself is large.

### MEDIUM
* Nails visibly extend beyond the fingertip.
* The extension is noticeable but not very long.
* The nails have a balanced, moderate length.

### LONG
* Nails extend significantly beyond the fingertip.
* The overall appearance is clearly long.
* Very long or dramatic nail extensions should be classified as LONG.

If the image does not provide enough information to confidently determine the length, \
return "uncertain".

## 2. DESIGN COMPLEXITY

Classify the design into one of these three categories:

### MINIMAL
Use MINIMAL when the design requires relatively little nail art work.

Examples include:
* Solid color
* Simple French manicure
* Simple ombré
* Chrome or glazed effect
* Cat-eye effect
* One simple technique applied consistently across the nails
* Very simple lines or dots
* 1–2 accent nails
* A small number of simple decorative elements

MINIMAL does NOT necessarily mean that the nails are plain. A visually impressive effect \
can still be MINIMAL if it requires little additional manual nail art work.

### MEDIUM
Use MEDIUM when the design requires a moderate amount of nail art work or combines \
several relatively simple techniques.

Examples include:
* Nail art on most or all nails
* French combined with another effect such as chrome
* Multiple colors or patterns
* Simple flowers
* Simple swirls or abstract patterns
* Several decorative elements
* More detailed French variations
* Multiple techniques combined together
* Moderate use of gems, charms, or other decorations

MEDIUM should generally involve more work than MINIMAL but should not require extensive \
detailed hand painting or highly intricate decoration.

### COMPLEX
Use COMPLEX when the design requires substantial manual work, precision, detail, or \
multiple intricate elements.

Examples include:
* Detailed hand-painted artwork
* Characters or portraits
* Highly detailed flowers or illustrations
* Different intricate designs on multiple/all nails
* 3D nail art
* Intricate sculpted elements
* Extensive use of charms, gems, or decorations
* Highly detailed patterns
* Several advanced techniques combined
* Designs that would reasonably require significantly more time and precision than a \
typical nail art set

Focus on the **amount of work, detail, precision, and techniques required**, rather than \
simply how visually impressive the design looks.

## 3. IDENTIFY INDIVIDUAL DESIGN ELEMENTS

In addition to the overall complexity, identify which elements are visible.

Check for:
* French manicure
* Chrome
* Cat-eye
* Ombre
* Solid color
* Simple line art
* Simple abstract art
* Floral design
* Detailed hand-painted art
* Characters/illustrations
* Gems/rhinestones
* Charms
* 3D elements
* Multiple colors
* Different designs on different nails
* Other visible techniques

Only mark an element as present if it is reasonably visible in the image.

## 4. EXTENSIONS

Determine whether the image appears to show natural nails or nail extensions.

This classification maps to the two service categories offered:
* **Regular** — natural nails (no extensions)
* **Extensions** — nail extensions (gel, acrylic, or other build-up)

Output one of:
* "natural" (maps to Regular service)
* "extensions" (maps to Extensions service)
* "uncertain" (if it cannot be determined from the photo)

Do not assume extensions simply because the nails are long.

## 5. CONFIDENCE

For each major classification, provide a confidence score between 0 and 1.

If the image is blurry, poorly lit, partially visible, or does not show enough \
information, reduce the confidence score.

## 6. IMPORTANT RULES

* Do not estimate a price.
* Do not invent details that cannot be seen.
* Do not judge the design based on personal taste.
* Focus on visible characteristics and the amount of work likely required.
* If something cannot be determined from the photo, use "uncertain".
* Be consistent in your classifications.
* A design can look complicated while still be MINIMAL if it requires little additional work.
* A design can look simple but be COMPLEX if it involves detailed hand painting or \
technically difficult work.

## OUTPUT FORMAT

Return ONLY valid JSON in this exact structure:

{
  "length": {
    "classification": "short | medium | long | uncertain",
    "confidence": 0.0
  },
  "design_complexity": {
    "classification": "minimal | medium | complex | uncertain",
    "confidence": 0.0
  },
  "extensions": {
    "classification": "natural | extensions | uncertain",
    "confidence": 0.0
  },
  "design_elements": {
    "french": false,
    "chrome": false,
    "cat_eye": false,
    "ombre": false,
    "solid_color": false,
    "simple_line_art": false,
    "simple_abstract_art": false,
    "floral_design": false,
    "detailed_hand_painted_art": false,
    "characters_or_illustrations": false,
    "gems_or_rhinestones": false,
    "charms": false,
    "three_d_elements": false,
    "multiple_colors": false,
    "different_designs_on_different_nails": false
  },
  "visible_details": "Brief description of what is visible in the image.",
  "uncertainties": "Briefly describe anything that cannot be reliably determined from the image."
}
"""

# Maps AI design_complexity values to our DB design tier names
_COMPLEXITY_TO_TIER = {
    DesignComplexityClassification.MINIMAL: "Simple",
    DesignComplexityClassification.MEDIUM: "Medium",
    DesignComplexityClassification.COMPLEX: "Advanced",
}

# Maps AI extensions classification to our DB nail type names
_EXTENSIONS_TO_NAIL_TYPE = {
    ExtensionsClassification.EXTENSIONS: "Extensions",
    ExtensionsClassification.NATURAL: "Regular",
    ExtensionsClassification.UNCERTAIN: "Regular",  # default to Regular when uncertain
}


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
        raise ValidationError(
            "Could not classify the uploaded image. Please try another photo."
        )

    return classification


def _map_to_nail_type_name(classification: NailClassification) -> str:
    """Map the AI's extensions classification to a nail type DB name."""
    return _EXTENSIONS_TO_NAIL_TYPE[classification.extensions]


def _map_to_design_tier_name(classification: NailClassification) -> str:
    """Map the AI's design_complexity classification to a design tier DB name."""
    if classification.design_complexity == DesignComplexityClassification.UNCERTAIN:
        # Default to Medium when the AI is uncertain about complexity
        return "Medium"
    return _COMPLEXITY_TO_TIER[classification.design_complexity]


def _overall_confidence(classification: NailClassification) -> str:
    """Derive an overall confidence string from the individual scores."""
    scores = [
        classification.extensions_confidence,
        classification.design_complexity_confidence,
    ]
    avg = sum(scores) / len(scores)
    if avg >= 0.8:
        return "high"
    elif avg >= 0.5:
        return "medium"
    return "low"


async def analyze_nails(
    image_bytes: bytes,
    media_type: str,
    db: AsyncSession,
) -> NailAnalysisResponse:
    """Classify a nail photo, then price it server-side from the active DB rows.
    The AI never sees or produces prices — it only picks the classifications."""
    classification = _classify_image(image_bytes, media_type)

    nail_type_name = _map_to_nail_type_name(classification)
    design_tier_name = _map_to_design_tier_name(classification)

    result = await db.execute(
        select(NailType).where(
            NailType.name == nail_type_name,
            NailType.is_active,
        )
    )
    nail_type = result.scalar_one_or_none()

    result = await db.execute(
        select(DesignTier).where(
            DesignTier.name == design_tier_name,
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

    reasoning = classification.visible_details[:MAX_REASONING_LENGTH]

    return NailAnalysisResponse(
        nail_type_id=nail_type.id,
        design_tier_id=design_tier.id,
        nail_type=nail_type.name,
        design_tier=design_tier.name,
        estimated_price=estimated_price,
        estimated_duration_minutes=estimated_duration,
        confidence=_overall_confidence(classification),
        reasoning=reasoning,
        length=classification.length.value,
        design_elements=None,
    )
