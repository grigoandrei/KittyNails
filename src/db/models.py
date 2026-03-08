import enum
from sqlalchemy import Column, Integer, String, Numeric, Enum, Time, Date, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class NailService(Base):
     __tablename__ = "nail_services"

     id = Column(Integer, primary_key=True, index=True)
     name = Column(String(100), nullable=False)
     description = Column(String(500), nullable=True)
     duration_minutes=Column(Integer, nullable=False)
     price = Column(Numeric(10, 2), nullable=False)
     

class AppointmentStatus(enum.Enum):
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    COMPLETED = "completed"

class Appointment(Base):
    __tablename__ = "appointment"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    client_email = Column(String(50), nullable=True)
    service_id = Column(Integer, ForeignKey("nail_services.id"))
    service = relationship("NailService")
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(AppointmentStatus), nullable=False)
   

class WeeklyAvailability(Base):
    __tablename__ = "weekly_availability"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

class BlockedTime(Base):
    __tablename__ = "blocked_time"

    id = Column(Integer, primary_key=True, index=True)
    blocked_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    reason=Column(String(200), nullable=True)