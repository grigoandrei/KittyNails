from enum import IntEnum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import time, date

class DaysOfWeek(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class WeeklyAvailabilityCreate(BaseModel):
    day_of_week: DaysOfWeek
    start_time: time = Field(..., description="When the work day starts")
    end_time: time = Field(..., description="When the work day ends")

    @field_validator("end_time")
    @classmethod
    def end_after_starts(cls, v: time, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

class WeeklyAvailability(WeeklyAvailabilityCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class BlockedTimeCreate(BaseModel):
    blocked_date: date
    start_time: time | None = None  # None means entire day is blocked
    end_time: time | None = None
    reason: str | None = None

class BlockedTimeResponse(BlockedTimeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class TimeSlot(BaseModel):
    start_time: time
    end_time: time
    available: bool = True

class DaySchedule(BaseModel):
    date: date
    slots: list[TimeSlot]
    is_working_day: bool
