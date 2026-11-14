import uuid
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class MonthlySetModel(Base):
    """A one-of-one nail design the artist wants to do. Each model can be
    booked by exactly one client. Its availability is derived from its
    appointments, never stored, so it can't drift."""

    __tablename__ = "monthly_set_models"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Admin can hide a model from the site without deleting it.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
