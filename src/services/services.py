from sqlalchemy.orm import Session
from db.models import NailService
from models.service import NailServiceCreate, NailServiceUpdate

def get_all_services(db: Session):
    return db.query(NailService).all()

def get_service_by_id(db: Session, service_id: int):
    return db.query(NailService).filter(NailService.id == service_id).first()

def create_service(db: Session, service: NailServiceCreate):
    db_service = NailService(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_service(db: Session, service_id: int, service: NailServiceUpdate):
    db_service = db.query(NailService).filter(NailService.id == service_id).first()
    if not db_service:
        return None
    
    update_data = service.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service



