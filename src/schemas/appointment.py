from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AppointmentCreate(BaseModel):
    nail_type_id: UUID
    design_tier_id: UUID | None = None
    client_email: EmailStr
    start_time: datetime
    # Carried through from the AI analysis step so we can persist it on the
    # appointment. Optional — a booking can be made without an analysis.
    ai_confidence: str | None = Field(default=None, max_length=20)
    ai_reasoning: str | None = Field(default=None, max_length=1000)

    @field_validator("start_time")
    @classmethod
    def is_in_the_future(cls, start_time: datetime) -> datetime:
        now = datetime.now(tz=start_time.tzinfo)
        if start_time <= now:
            raise ValueError("Date cannot be in the past!")
        return start_time


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nail_type_id: UUID
    design_tier_id: UUID | None
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


class CheckoutSessionResponse(BaseModel):
    """Returned from the create-checkout-session endpoint."""

    checkout_url: str
    session_id: str
    appointment_id: UUID
