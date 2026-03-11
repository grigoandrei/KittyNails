from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.service import NailServiceResponse, NailServiceCreate, NailServiceUpdate
from services.services import get_all_services, create_service, update_service
from dependencies import require_owner

router = APIRouter(prefix="/services", tags=["services"])

@router.get("/", response_model=list[NailServiceResponse])
def list_services(db: Session = Depends(get_db)):
    return get_all_services(db)

@router.post("/", response_model=NailServiceResponse, status_code=201)
def create_services(service: NailServiceCreate, db: Session = Depends(get_db), _owner: str = Depends(require_owner)):
    return create_service(db, service=service)

@router.put("/{service_id}", response_model=NailServiceResponse)
def update_services(service_id: int, service: NailServiceUpdate, db: Session = Depends(get_db), _owner: str = Depends(require_owner)):
    result = update_service(db, service=service, service_id=service_id)
    if not result:
        raise HTTPException(status_code=404, detail="Service not found")
    return result
