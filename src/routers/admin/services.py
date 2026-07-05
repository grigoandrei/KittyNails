from src.schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.service_crud import create_service, update_service, get_all_services
from src.auth import get_current_admin
from uuid import UUID

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.post("/api/admin/services", response_model=ServiceResponse, status_code=201)
async def create(data: ServiceCreate, db: AsyncSession = Depends(get_db)):
    return await create_service(data, db)

@router.put("/api/admin/services/{service_id}", response_model=ServiceResponse)
async def update(service_id: UUID, data: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    return await update_service(service_id, data, db)

@router.get("/api/admin/services", response_model=list[ServiceResponse])
async def get_services(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_all_services(db, skip=skip, limit=limit)