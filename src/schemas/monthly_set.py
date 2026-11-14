from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

TITLE_MAX = 80
DESCRIPTION_MAX = 500
DURATION_MIN = 15
DURATION_MAX = 600
PRICE_MAX = 9999


class MonthlySetState(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    BOOKED = "booked"
    HIDDEN = "hidden"


class MonthlySetUpdate(BaseModel):
    """Partial admin edit. The photo is replaced through its own endpoint."""

    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX)
    price: float | None = Field(default=None, gt=0, le=PRICE_MAX)
    duration_minutes: int | None = Field(
        default=None, ge=DURATION_MIN, le=DURATION_MAX
    )
    # Send an empty string to clear the description.
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class MonthlySetPublicResponse(BaseModel):
    id: UUID
    title: str
    price: float
    duration_minutes: int
    description: str | None
    image_url: str | None


class MonthlySetAdminResponse(MonthlySetPublicResponse):
    is_active: bool
    sort_order: int
    state: MonthlySetState
    # True once any appointment ever referenced the model. Such models can't be
    # deleted because appointment history points at them.
    has_bookings: bool
    appointment_id: UUID | None = None
    client_email: str | None = None
    appointment_start: datetime | None = None
    created_at: datetime
    updated_at: datetime
