from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.appointment import AppointmentCreate, AppointmentResponse
from models.availability import TimeSlot
from services.appointment_service import AppointmentService
from datetime import date

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.get("/", response_model=list[AppointmentResponse])
def list_appointments_by_date(date: date, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    return service.get_appointments_by_date(date)

@router.get("/available", response_model=list[TimeSlot])
def get_available_slots(date: date, service_id: int, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    return service.get_available_slots(date, service_id)

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(booking: AppointmentCreate, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        return service.book_appointment(booking=booking)
    except ValueError as e:
        msg = str(e)
        if "no longer available" in msg:
            raise HTTPException(status_code=409, detail=msg)
        elif "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    appointment = service.get_appointment(appointment_id=appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    service = AppointmentService(db)
    try:
        service.cancel_appointment(appointment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))