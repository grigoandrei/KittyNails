import uuid
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Status(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    BOOKED = "BOOKED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    nail_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nail_types.id"))
    design_tier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("design_tiers.id"), nullable=True
    )
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[Status] = mapped_column(SAEnum(Status), nullable=False)
    quoted_price: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    ai_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Stripe fields
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
