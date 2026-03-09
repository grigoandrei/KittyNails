from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, time, datetime
from models.service import NailServiceResponse


class AppointmentCreate(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100)
    client_phone: str = Field(..., min_length=7, max_length=20)
    client_email: str | None = Field(default=None)
    service_id: int = Field(..., gt=0)
    appointment_date: date
    appointment_time: time

    @field_validator("appointment_date")
    @classmethod
    def date_must_be_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Appointment date must be today or in the future")
        return v

    @field_validator("appointment_time")
    @classmethod
    def time_must_be_on_quarter_hour(cls, v: time) -> time:
        if v.minute % 15 != 0:
            raise ValueError("Appointment time must be on a 15-minute boundary")
        return v

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    client_phone: str
    client_email: str | None
    service: NailServiceResponse
    appointment_date: date
    appointment_time: time
    end_time: time
    status: str
    created_at: datetime