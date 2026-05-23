from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import time, datetime

class AvailabilityRulesCreate(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time

class AvailabilityRulesUpdate(BaseModel):
    day_of_week: int | None = None
    start_time: time | None = None
    end_time: time | None = None

class AvailabilityRulesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    created_at: datetime
