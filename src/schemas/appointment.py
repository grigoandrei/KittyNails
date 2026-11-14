from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class AppointmentCreate(BaseModel):
    # Exactly one of nail_type_id (regular service) or monthly_set_model_id
    # (one-of-one artist design) must be set.
    nail_type_id: UUID | None = None
    design_tier_id: UUID | None = None
    monthly_set_model_id: UUID | None = None
    client_email: EmailStr
    start_time: datetime
    # Carried through from the AI analysis step so we can persist it on the
    # appointment. Optional — a booking can be made without an analysis.
    ai_confidence: str | None = Field(default=None, max_length=20)
    ai_reasoning: str | None = Field(default=None, max_length=1000)
    # S3 object key of the uploaded nail photo, carried over from the analyze
    # step. Optional — Japanese Manicure and analysis-free bookings omit it.
    image_key: str | None = Field(default=None, max_length=512)
    # Client requested removal of existing nails — adds a flat surcharge
    # (NAIL_REMOVAL_PRICE) to the price, applied server-side. No duration change.
    needs_removal: bool = False

    @field_validator("start_time")
    @classmethod
    def is_in_the_future(cls, start_time: datetime) -> datetime:
        now = datetime.now(tz=start_time.tzinfo)
        if start_time <= now:
            raise ValueError("Date cannot be in the past!")
        return start_time

    @model_validator(mode="after")
    def one_service(self) -> "AppointmentCreate":
        if (self.nail_type_id is None) == (self.monthly_set_model_id is None):
            raise ValueError("Choose either a nail type or a monthly set.")
        if self.monthly_set_model_id is not None and self.design_tier_id is not None:
            raise ValueError("Monthly sets don't use a design tier.")
        return self


class AppointmentUpdate(BaseModel):
    """Admin edit of an existing appointment (partial). Duration and price are
    explicit overrides. Without a price override, the current price is kept and
    only adjusted by the removal fee when needs_removal changes."""

    start_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=600)
    needs_removal: bool | None = None
    quoted_price: float | None = Field(default=None, ge=0, le=9999)

    @field_validator("start_time")
    @classmethod
    def is_in_the_future(cls, start_time: datetime | None) -> datetime | None:
        if start_time is None:
            return start_time
        now = datetime.now(tz=start_time.tzinfo)
        if start_time <= now:
            raise ValueError("Date cannot be in the past!")
        return start_time


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nail_type_id: UUID | None
    design_tier_id: UUID | None
    monthly_set_model_id: UUID | None = None
    client_email: str
    start_time: datetime
    end_time: datetime
    status: str
    quoted_price: float
    ai_confidence: str | None
    ai_reasoning: str | None
    stripe_session_id: str | None = None
    stripe_payment_intent_id: str | None = None
    created_at: datetime
    needs_removal: bool = False
    source: str = "web"
    # Presigned S3 URL for the client's uploaded photo, populated for admin
    # responses. None when there's no photo or storage is unavailable.
    image_url: str | None = None


class CheckoutSessionResponse(BaseModel):
    """Returned from the create-checkout-session endpoint."""

    checkout_url: str
    session_id: str
    appointment_id: UUID
