from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field
from uuid import UUID
from datetime import datetime, timezone

class AppointmentCreate(BaseModel):
    service_id: UUID
    client_email: EmailStr
    start_time: datetime
    @field_validator('start_time')
    @classmethod
    def is_in_the_future(cls, start_time: datetime) -> datetime:
        if start_time <= datetime.now(tz=timezone.utc):
            raise ValueError("Date cannot be in the past!")
        return start_time

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    service_id: UUID
    client_email: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime