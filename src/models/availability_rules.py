from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Time, DateTime
from src.database import Base
from datetime import time, datetime, timezone
import uuid
from uuid import uuid4

class AvailabilityRules(Base):
    __tablename__ = "availability_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
