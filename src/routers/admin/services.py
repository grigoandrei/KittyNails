from src.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.service_crud import create_service, update_service, get_all_services
from uuid import UUID

router = APIRouter()

@router.post("/api/admin/services", response_model=ServiceResponse, status_code=201)
async def create(data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    try:
        service = await create_service(data, db)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))

    return service

@router.put("/api/admin/services/{service_id}", response_model=ServiceResponse)
async def update(service_id: UUID, data: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    try:
        service = await update_service(service_id, data, db)
    except ValueError as e:
        if "not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))

    return service

@router.get("/api/admin/services", response_model=list[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await get_all_services(db)
    return result