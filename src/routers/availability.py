from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.availability import WeeklyAvailabilityCreate, BlockedTimeCreate, WeeklyAvailability, BlockedTimeCreate, BlockedTimeResponse, DaySchedule, TimeSlot
from services.availability_service import set_weekly_availability, get_availability_for_date, block_time, get_blocked_times_for_date
from datetime import date

router = APIRouter(prefix="/availability", tags=["availability"])

@router.get("/", response_model=DaySchedule)
def get_schedule(date: date, db: Session = Depends(get_db)):
    availability = get_availability_for_date(db, date)
    _blocked = get_blocked_times_for_date(db, date)
    if not availability:
        return DaySchedule(date=date, slots=[], is_working_day=False)

    slots = [TimeSlot(start_time=availability.start_time, end_time=availability.end_time)]

    return DaySchedule(date=date, slots= slots, is_working_day=True)

@router.put("/weekly", response_model=list[WeeklyAvailability])
def update_weekly_availability(schedule: list[WeeklyAvailabilityCreate], db: Session=Depends(get_db)):
    return set_weekly_availability(db, schedule)

@router.post("/block", response_model=BlockedTimeResponse, status_code=201)
def create_blocked_time(block: BlockedTimeCreate, db: Session = Depends(get_db)):
    return block_time(db, block)