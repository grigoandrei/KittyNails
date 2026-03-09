"""
Property-based tests for Pydantic model validation.

Property 3: Future-Only Booking — past dates are always rejected, future dates accepted.
Property 5: Availability Bounds — end_time > start_time is always enforced.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import date, time, timedelta
from hypothesis import given, strategies as st, assume, settings
from pydantic import ValidationError
import pytest

from models.appointment import AppointmentCreate
from models.availability import WeeklyAvailabilityCreate, DaysOfWeek


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_appointment_kwargs(d: date, t: time) -> dict:
    """Build a valid AppointmentCreate dict with the given date and time."""
    return {
        "client_name": "Test Client",
        "client_phone": "555-0100",
        "service_id": 1,
        "appointment_date": d,
        "appointment_time": t,
    }


QUARTER_HOUR_TIMES = st.sampled_from(
    [time(h, m) for h in range(24) for m in (0, 15, 30, 45)]
)


# ---------------------------------------------------------------------------
# Property 3 — Future-Only Booking
# ---------------------------------------------------------------------------

@given(d=st.dates(max_value=date.today() - timedelta(days=1)))
@settings(max_examples=200)
def test_past_dates_are_always_rejected(d: date):
    """Any date strictly before today must be rejected."""
    with pytest.raises(ValidationError, match="Appointment date must be today or in the future"):
        AppointmentCreate(**make_appointment_kwargs(d, time(10, 0)))


@given(d=st.dates(min_value=date.today(), max_value=date(2099, 12, 31)))
@settings(max_examples=200)
def test_today_and_future_dates_are_accepted(d: date):
    """Today or any future date must be accepted (with a valid quarter-hour time)."""
    appt = AppointmentCreate(**make_appointment_kwargs(d, time(10, 0)))
    assert appt.appointment_date == d


# ---------------------------------------------------------------------------
# Property 5 — Availability Bounds (end_time > start_time)
# ---------------------------------------------------------------------------

@given(
    day=st.sampled_from(list(DaysOfWeek)),
    t=st.times(),
)
@settings(max_examples=200)
def test_equal_start_and_end_time_rejected(day: DaysOfWeek, t: time):
    """end_time == start_time must always be rejected."""
    with pytest.raises(ValidationError, match="end_time must be after start_time"):
        WeeklyAvailabilityCreate(day_of_week=day, start_time=t, end_time=t)


@given(
    day=st.sampled_from(list(DaysOfWeek)),
    start=st.times(),
    end=st.times(),
)
@settings(max_examples=200)
def test_end_before_or_equal_start_rejected(day: DaysOfWeek, start: time, end: time):
    """Any end_time <= start_time must be rejected."""
    assume(end <= start)
    with pytest.raises(ValidationError, match="end_time must be after start_time"):
        WeeklyAvailabilityCreate(day_of_week=day, start_time=start, end_time=end)


@given(
    day=st.sampled_from(list(DaysOfWeek)),
    start=st.times(max_value=time(23, 58)),
    end=st.times(),
)
@settings(max_examples=200)
def test_valid_availability_accepted(day: DaysOfWeek, start: time, end: time):
    """Any end_time strictly after start_time must be accepted."""
    assume(end > start)
    avail = WeeklyAvailabilityCreate(day_of_week=day, start_time=start, end_time=end)
    assert avail.start_time == start
    assert avail.end_time == end
    assert avail.day_of_week == day
