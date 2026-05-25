from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class BlockedTimeCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    reason: str | None = None

class BlockedTimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    start_time: datetime
    end_time: datetime
    reason: str | None = None
    created_at: datetime