from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from src.database import Base
from datetime import datetime, timezone
import uuid
from uuid import uuid4

class BlockedTime(Base):
    __tablename__ = "blocked_times"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))