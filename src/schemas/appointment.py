from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class AppointmentCreate(BaseModel):
    service_id: UUID
    client_email: str
    start_time: datetime

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    service_id: UUID
    client_email: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime