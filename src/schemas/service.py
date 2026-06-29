from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class ServiceCreate(BaseModel):
    name: str = Field(max_length=100)
    duration_minutes: int = Field(gt=0)
    price: float = Field(gt=0)

class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None ,max_length=100)
    duration_minutes: int | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None

class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    duration_minutes: int
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime