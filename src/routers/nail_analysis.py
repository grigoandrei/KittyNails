from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.exceptions import ValidationError
from src.limiter import limiter
from src.schemas.nail_analysis import NailAnalysisResponse
from src.services.nail_analysis_service import SUPPORTED_MEDIA_TYPES, analyze_nails

router = APIRouter()

# Bedrock caps request payloads at 20 MB; keep client uploads well under that
# after base64 expansion (~33% overhead). 5 MB of raw image is plenty for a
# phone photo of nails.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.post("/api/analyze-nails", response_model=NailAnalysisResponse)
@limiter.limit("5/hour")
async def analyze(
    request: Request,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if image.content_type not in SUPPORTED_MEDIA_TYPES:
        raise ValidationError(
            f"Unsupported image type. Please upload one of: {', '.join(sorted(SUPPORTED_MEDIA_TYPES))}."
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise ValidationError("The uploaded file is empty.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Image is too large. Please upload an image under 5 MB.")

    return await analyze_nails(image_bytes, image.content_type, db)
