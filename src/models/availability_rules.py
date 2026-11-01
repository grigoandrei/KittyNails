import uuid
from datetime import UTC, datetime, time
from uuid import uuid4

from sqlalchemy import DateTime, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class AvailabilityRules(Base):
    __tablename__ = "availability_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
