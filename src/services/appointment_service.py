from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session
from db.models import NailService, WeeklyAvailability, BlockedTime, Appointment, AppointmentStatus
from models.appointment import AppointmentCreate
from models.availability import TimeSlot

class AppointmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_slots(self, target_date: date, service_id: int) -> list[TimeSlot]:
        service = self.db.query(NailService).filter(NailService.id == service_id).first()
        if not service:
            return []
        duration = timedelta(minutes=service.duration_minutes)

        availability = (
            self.db.query(WeeklyAvailability)
            .filter(WeeklyAvailability.day_of_week == target_date.weekday())
            .first()
        )
        if not availability:
            return []

        blocked_times = (
            self.db.query(BlockedTime).filter(BlockedTime.blocked_date == target_date)
            .all()
        )
        booked = (
            self.db.query(Appointment)
            .filter(Appointment.status == AppointmentStatus.CONFIRMED,
            Appointment.appointment_date == target_date)
            .all()

        )

        unavailable = []
        for b in blocked_times:
            if b.start_time is None:
                return []
            unavailable.append((
                datetime.combine(target_date, b.start_time),
                datetime.combine(target_date, b.end_time)
            ))
        for a in booked:
            unavailable.append((
                datetime.combine(target_date, a.appointment_time),
                datetime.combine(target_date, a.end_time)
            ))

        window_start = datetime.combine(target_date, availability.start_time)
        window_end = datetime.combine(target_date, availability.end_time)

        slots = []
        current = window_start
        while current + duration <= window_end:
             slot_end = current + duration
             overlaps = any(
                current < u_end and slot_end > u_start
                for u_start, u_end in unavailable
             )
             if not overlaps:
                slots.append(TimeSlot(
                    start_time=current.time(),
                    end_time=slot_end.time()
                ))
             current += timedelta(minutes=15)
        return slots

    def book_appointment(self, booking: AppointmentCreate) -> Appointment:
        service = self.db.query(NailService).filter(NailService.id == booking.service_id).first()
        if not service:
            raise ValueError("Service not found")

        start_dt = datetime.combine(booking.appointment_date, booking.appointment_time)
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        conflict = (
            self.db.query(Appointment)
            .filter(
                Appointment.appointment_date == booking.appointment_date,
                Appointment.status == AppointmentStatus.CONFIRMED,
                Appointment.appointment_time < end_dt.time(),
                Appointment.end_time > booking.appointment_time,
            )
            .first()
        )
        if conflict:
            raise ValueError("Time slot is no longer available!")
        
        appointment = Appointment(
            client_name=booking.client_name,
            client_phone=booking.client_phone,
            client_email=booking.client_email,
            service_id=booking.service_id,
            appointment_date=booking.appointment_date,
            appointment_time=booking.appointment_time,
            end_time=end_dt.time(),
            status=AppointmentStatus.CONFIRMED,
        )
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def cancel_appointment(self, appointment_id: int) -> Appointment:
        appointment = (
            self.db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if not appointment:
            raise ValueError("Appointment not found")
        
        appointment.status = AppointmentStatus.CANCELED
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get_appointment(self, appointment_id: int) -> Appointment | None:
        return(
            self.db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .first()
        )