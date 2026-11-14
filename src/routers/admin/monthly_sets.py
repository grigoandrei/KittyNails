from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_admin
from src.database import get_db
from src.schemas.monthly_set import (
    DESCRIPTION_MAX,
    DURATION_MAX,
    DURATION_MIN,
    PRICE_MAX,
    TITLE_MAX,
    MonthlySetAdminResponse,
    MonthlySetUpdate,
)
from src.services import monthly_set_service
from src.services.uploads import read_image

router = APIRouter(
    prefix="/api/admin/monthly-sets",
    tags=["admin-monthly-sets"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=list[MonthlySetAdminResponse])
async def list_designs(db: AsyncSession = Depends(get_db)):
    return await monthly_set_service.list_all(db)


@router.post("", response_model=MonthlySetAdminResponse, status_code=201)
async def create_design(
    title: str = Form(..., min_length=1, max_length=TITLE_MAX),
    price: float = Form(..., gt=0, le=PRICE_MAX),
    duration_minutes: int = Form(..., ge=DURATION_MIN, le=DURATION_MAX),
    description: str | None = Form(default=None, max_length=DESCRIPTION_MAX),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await read_image(image)
    model = await monthly_set_service.create_model(
        db,
        title=title,
        price=price,
        duration_minutes=duration_minutes,
        description=description,
        image_bytes=image_bytes,
        content_type=image.content_type,
    )
    return await monthly_set_service.admin_response(db, model)


@router.put("/{model_id}", response_model=MonthlySetAdminResponse)
async def update_design(
    model_id: UUID, data: MonthlySetUpdate, db: AsyncSession = Depends(get_db)
):
    model = await monthly_set_service.update_model(db, model_id, data)
    return await monthly_set_service.admin_response(db, model)


@router.put("/{model_id}/image", response_model=MonthlySetAdminResponse)
async def replace_design_image(
    model_id: UUID,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    image_bytes = await read_image(image)
    model = await monthly_set_service.replace_image(
        db, model_id, image_bytes, image.content_type
    )
    return await monthly_set_service.admin_response(db, model)


@router.delete("/{model_id}", status_code=204)
async def delete_design(model_id: UUID, db: AsyncSession = Depends(get_db)):
    await monthly_set_service.delete_model(db, model_id)
