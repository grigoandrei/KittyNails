from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: float

class ServiceUpdate(BaseModel):
    name: str | None = None
    duration_minutes: int | None = None
    price: float | None = None

class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    duration_minutes: int
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime