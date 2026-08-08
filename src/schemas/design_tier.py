from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DesignTierCreate(BaseModel):
    name: str = Field(max_length=100)
    duration_minutes: int = Field(ge=0)
    price: float = Field(ge=0)
    sort_order: int = Field(default=0, ge=0)


class DesignTierUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    duration_minutes: int | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class DesignTierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    duration_minutes: int
    price: float
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
