from src.schemas.nail_type import NailTypeCreate, NailTypeResponse, NailTypeUpdate
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.nail_type_crud import create_nail_type, update_nail_type, get_all_nail_types
from src.auth import get_current_admin
from uuid import UUID

router = APIRouter(dependencies=[Depends(get_current_admin)])

@router.post("/api/admin/nail-types", response_model=NailTypeResponse, status_code=201)
async def create(data: NailTypeCreate, db: AsyncSession = Depends(get_db)):
    return await create_nail_type(data, db)

@router.put("/api/admin/nail-types/{nail_type_id}", response_model=NailTypeResponse)
async def update(nail_type_id: UUID, data: NailTypeUpdate, db: AsyncSession = Depends(get_db)):
    return await update_nail_type(nail_type_id, data, db)

@router.get("/api/admin/nail-types", response_model=list[NailTypeResponse])
async def get_nail_types(skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    return await get_all_nail_types(db, skip=skip, limit=limit)
