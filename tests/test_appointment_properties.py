"""
Property-based tests for appointment booking logic.

Property 1: No Double Booking — booking the same slot twice is always rejected.
Property 2: Slot Consistency — available slots = (working hours − blocked − booked) / duration.
Property 4: Duration Integrity — end_time == start_time + service.duration_minutes.
Property 6: Cancellation Reversibility — cancelling frees the slot back up.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from contextlib import contextmanager
from datetime import date, time, timedelta, datetime
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base
from db.models import NailService, WeeklyAvailability, BlockedTime
from models.appointment import AppointmentCreate
from services.appointment_service import AppointmentService

# ---------------------------------------------------------------------------
# Test database — fresh tables per test invocation via context manager
# ---------------------------------------------------------------------------

test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@contextmanager
def fresh_db():
    """Yield a clean DB session with empty tables, then tear down."""
    Base.metadata.create_all(bind=test_engine)
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSession(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# A future Monday we can safely use for all tests.
FUTURE_MONDAY = date(2026, 3, 16)


def seed_service(db, duration_minutes=60) -> NailService:
    svc = NailService(
        name="Test Service",
        description="For testing",
        duration_minutes=duration_minutes,
        price=Decimal("30.00"),
    )
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def seed_availability(db, day_of_week=0, start=time(9, 0), end=time(17, 0)):
    avail = WeeklyAvailability(day_of_week=day_of_week, start_time=start, end_time=end)
    db.add(avail)
    db.commit()
    return avail


def seed_blocked_time(db, blocked_date, start=None, end=None):
    bt = BlockedTime(blocked_date=blocked_date, start_time=start, end_time=end)
    db.add(bt)
    db.commit()
    return bt


def make_booking(service_id: int, appt_date: date, appt_time: time) -> AppointmentCreate:
    return AppointmentCreate(
        client_name="Test Client",
        client_phone="555-0100",
        service_id=service_id,
        appointment_date=appt_date,
        appointment_time=appt_time,
    )


# Strategy: quarter-hour times within a typical working window (09:00–16:00)
QUARTER_HOUR_WORK_TIMES = st.sampled_from(
    [time(h, m) for h in range(9, 16) for m in (0, 15, 30, 45)]
)

# Strategy: service durations that are multiples of 15 (15–120 min)
SERVICE_DURATIONS = st.sampled_from([15, 30, 45, 60, 75, 90, 105, 120])


# ---------------------------------------------------------------------------
# Property 1 — No Double Booking
# ---------------------------------------------------------------------------

@given(slot_time=QUARTER_HOUR_WORK_TIMES)
@settings(max_examples=50)
def test_no_double_booking(slot_time: time):
    """Booking the same slot twice must always fail on the second attempt."""
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=60)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday())

        service = AppointmentService(db)
        booking = make_booking(svc.id, FUTURE_MONDAY, slot_time)

        # First booking succeeds
        service.book_appointment(booking)

        # Second booking for the same slot must be rejected
        with pytest.raises(ValueError, match="no longer available"):
            service.book_appointment(booking)


# ---------------------------------------------------------------------------
# Property 2 — Slot Consistency
# ---------------------------------------------------------------------------

@given(duration=SERVICE_DURATIONS)
@settings(max_examples=30)
def test_slot_consistency_no_bookings(duration: int):
    """
    With no bookings or blocked times, available slots should equal
    the working window divided into service-duration chunks on 15-min steps.
    """
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=duration)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday(), start=time(9, 0), end=time(17, 0))

        service = AppointmentService(db)
        slots = service.get_available_slots(FUTURE_MONDAY, svc.id)

        # Manually compute expected slots
        window_start = datetime.combine(FUTURE_MONDAY, time(9, 0))
        window_end = datetime.combine(FUTURE_MONDAY, time(17, 0))
        dur = timedelta(minutes=duration)
        expected = []
        current = window_start
        while current + dur <= window_end:
            expected.append(current.time())
            current += timedelta(minutes=15)

        actual_starts = [s.start_time for s in slots]
        assert actual_starts == expected, (
            f"duration={duration}: expected {len(expected)} slots, got {len(actual_starts)}"
        )


@given(
    duration=SERVICE_DURATIONS,
    block_start_hour=st.integers(min_value=10, max_value=14),
)
@settings(max_examples=30)
def test_slot_consistency_with_blocked_time(duration: int, block_start_hour: int):
    """Blocked time should remove exactly the slots that overlap with it."""
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=duration)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday(), start=time(9, 0), end=time(17, 0))

        block_start = time(block_start_hour, 0)
        block_end = time(block_start_hour + 1, 0)
        seed_blocked_time(db, FUTURE_MONDAY, start=block_start, end=block_end)

        service = AppointmentService(db)
        slots = service.get_available_slots(FUTURE_MONDAY, svc.id)

        # No returned slot should overlap with the blocked window
        block_start_dt = datetime.combine(FUTURE_MONDAY, block_start)
        block_end_dt = datetime.combine(FUTURE_MONDAY, block_end)
        for slot in slots:
            slot_start_dt = datetime.combine(FUTURE_MONDAY, slot.start_time)
            slot_end_dt = datetime.combine(FUTURE_MONDAY, slot.end_time)
            overlaps = slot_start_dt < block_end_dt and slot_end_dt > block_start_dt
            assert not overlaps, (
                f"Slot {slot.start_time}-{slot.end_time} overlaps blocked {block_start}-{block_end}"
            )


@given(
    duration=SERVICE_DURATIONS,
    booking_time=QUARTER_HOUR_WORK_TIMES,
)
@settings(max_examples=30)
def test_slot_consistency_with_booking(duration: int, booking_time: time):
    """
    After booking a slot, available slots should exclude any that overlap
    with the booked appointment.
    """
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=duration)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday(), start=time(9, 0), end=time(17, 0))

        service = AppointmentService(db)

        booked_start = datetime.combine(FUTURE_MONDAY, booking_time)
        booked_end = booked_start + timedelta(minutes=duration)
        window_end = datetime.combine(FUTURE_MONDAY, time(17, 0))
        assume(booked_end <= window_end)

        booking = make_booking(svc.id, FUTURE_MONDAY, booking_time)
        service.book_appointment(booking)

        slots = service.get_available_slots(FUTURE_MONDAY, svc.id)

        for slot in slots:
            slot_start_dt = datetime.combine(FUTURE_MONDAY, slot.start_time)
            slot_end_dt = datetime.combine(FUTURE_MONDAY, slot.end_time)
            overlaps = slot_start_dt < booked_end and slot_end_dt > booked_start
            assert not overlaps, (
                f"Slot {slot.start_time}-{slot.end_time} overlaps booked "
                f"{booking_time}-{booked_end.time()}"
            )


# ---------------------------------------------------------------------------
# Property 4 — Duration Integrity
# ---------------------------------------------------------------------------

@given(
    duration=SERVICE_DURATIONS,
    booking_time=QUARTER_HOUR_WORK_TIMES,
)
@settings(max_examples=50)
def test_duration_integrity(duration: int, booking_time: time):
    """end_time must always equal start_time + service.duration_minutes."""
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=duration)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday(), start=time(9, 0), end=time(17, 0))

        booked_start = datetime.combine(FUTURE_MONDAY, booking_time)
        expected_end = booked_start + timedelta(minutes=duration)
        window_end = datetime.combine(FUTURE_MONDAY, time(17, 0))
        assume(expected_end <= window_end)

        service = AppointmentService(db)
        booking = make_booking(svc.id, FUTURE_MONDAY, booking_time)
        appointment = service.book_appointment(booking)

        assert appointment.end_time == expected_end.time(), (
            f"Expected end_time {expected_end.time()}, got {appointment.end_time}"
        )


# ---------------------------------------------------------------------------
# Property 6 — Cancellation Reversibility
# ---------------------------------------------------------------------------

@given(
    duration=SERVICE_DURATIONS,
    booking_time=QUARTER_HOUR_WORK_TIMES,
)
@settings(max_examples=50)
def test_cancellation_reversibility(duration: int, booking_time: time):
    """
    Cancelling a confirmed appointment must return its time slot
    to the available pool.
    """
    with fresh_db() as db:
        svc = seed_service(db, duration_minutes=duration)
        seed_availability(db, day_of_week=FUTURE_MONDAY.weekday(), start=time(9, 0), end=time(17, 0))

        booked_start = datetime.combine(FUTURE_MONDAY, booking_time)
        expected_end = booked_start + timedelta(minutes=duration)
        window_end = datetime.combine(FUTURE_MONDAY, time(17, 0))
        assume(expected_end <= window_end)

        service = AppointmentService(db)

        # Snapshot slots before booking
        slots_before = service.get_available_slots(FUTURE_MONDAY, svc.id)
        starts_before = {s.start_time for s in slots_before}

        # Book, then cancel
        booking = make_booking(svc.id, FUTURE_MONDAY, booking_time)
        appointment = service.book_appointment(booking)
        service.cancel_appointment(appointment.id)

        # Slots after cancellation should match slots before booking
        slots_after = service.get_available_slots(FUTURE_MONDAY, svc.id)
        starts_after = {s.start_time for s in slots_after}

        assert starts_before == starts_after, (
            f"Slots not restored after cancellation. "
            f"Missing: {starts_before - starts_after}, "
            f"Extra: {starts_after - starts_before}"
        )
