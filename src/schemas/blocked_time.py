from pydantic import BaseModel, ConfigDict, model_validator
from uuid import UUID
from datetime import datetime

class BlockedTimeCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: str | None = None

    @model_validator(mode='after')
    def end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

class BlockedTimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    start_time: datetime
    end_time: datetime
    reason: str | None = None
    created_at: datetime