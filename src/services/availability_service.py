from sqlalchemy.orm import Session
from db.models import WeeklyAvailability as WeeklyAvailabilityModel
from models.availability import WeeklyAvailabilityCreate, BlockedTimeCreate
from datetime import date
from db.models import BlockedTime as BlockedTimeModel

def set_weekly_availability( db: Session, schedules: list[WeeklyAvailabilityCreate]) -> list[WeeklyAvailabilityModel]:
    results = []
    for schedule in schedules:
        existing = (
            db.query(WeeklyAvailabilityModel)
            .filter(WeeklyAvailabilityModel.day_of_week == schedule.day_of_week)
            .first()
        )
        if existing:
            existing.start_time = schedule.start_time
            existing.end_time = schedule.end_time
            results.append(existing)
        else:
            new_entry = WeeklyAvailabilityModel(
                day_of_week=schedule.day_of_week,
                start_time=schedule.start_time,
                end_time=schedule.end_time
            )
            db.add(new_entry)
            results.append(new_entry)
        
        db.commit()
        for r in results:
            db.refresh(r)
        return results

def get_availability_for_date(db: Session, target_date: date) -> WeeklyAvailabilityModel | None:
    day_of_week = target_date.weekday()
    return (
        db.query(WeeklyAvailabilityModel).filter(WeeklyAvailabilityModel.day_of_week == day_of_week).first()
    )

def block_time(db: Session, block: BlockedTimeCreate) -> BlockedTimeModel:
    blocked = BlockedTimeModel(
        blocked_date=block.blocked_date,
        start_time=block.start_time,
        end_time=block.end_time,
        reason=block.reason
    )
    db.add(blocked)
    db.commit()
    db.refresh(blocked)
    return blocked

def get_blocked_times_for_date(
    db: Session, target_date: date
) -> list[BlockedTimeModel]:
    return (
        db.query(BlockedTimeModel)
        .filter(BlockedTimeModel.blocked_date == target_date)
        .all()
    )

