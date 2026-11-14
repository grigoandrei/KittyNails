from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.limiter import limiter
from src.schemas.nail_analysis import NailAnalysisResponse
from src.services.nail_analysis_service import analyze_nails
from src.services.uploads import read_image

router = APIRouter()


@router.post("/api/analyze-nails", response_model=NailAnalysisResponse)
@limiter.limit("10/hour")
async def analyze(
    request: Request,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await read_image(image)
    return await analyze_nails(image_bytes, image.content_type, db)
