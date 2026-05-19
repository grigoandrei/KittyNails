from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy import Enum as SAEnum
import uuid
from enum import Enum
from uuid import uuid4
from src.database import Base
from datetime import datetime, timezone
from sqlalchemy import DateTime

class Status(Enum):
    BOOKED = "BOOKED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[Status] = mapped_column(SAEnum(Status), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))