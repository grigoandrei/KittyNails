from datetime import UTC, date, datetime, timedelta

from src.models.appointment import Appointment, Status
from src.models.nail_type import NailType
from src.services.income_service import weekly_income
from tests.conftest import async_session_test

# Fixed "now" so week boundaries are deterministic: Wednesday 2026-09-16.
NOW = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
START = date(2026, 9, 1)


async def _seed(rows):
    async with async_session_test() as db:
        nail_type = NailType(name="Regular", price=40, duration_minutes=90)
        db.add(nail_type)
        await db.flush()
        for start_time, status, price in rows:
            db.add(Appointment(
                nail_type_id=nail_type.id,
                client_email="c@example.com",
                start_time=start_time,
                end_time=start_time + timedelta(minutes=90),
                status=status,
                quoted_price=price,
            ))
        await db.commit()


async def _income():
    async with async_session_test() as db:
        return await weekly_income(db, START, now=NOW)


async def test_weekly_income_buckets_by_monday_week():
    await _seed([
        (datetime(2026, 9, 2, 10, tzinfo=UTC), Status.COMPLETED, 40),
        (datetime(2026, 9, 3, 10, tzinfo=UTC), Status.BOOKED, 55),
        (datetime(2026, 9, 9, 10, tzinfo=UTC), Status.BOOKED, 30),
    ])
    weeks = await _income()
    assert [w["week_start"] for w in weeks] == [
        date(2026, 8, 31), date(2026, 9, 7), date(2026, 9, 14)
    ]
    assert [w["income"] for w in weeks] == [95.0, 30.0, 0.0]
    assert [w["appointments"] for w in weeks] == [2, 1, 0]


async def test_weekly_income_skips_canceled_future_and_pre_start():
    await _seed([
        (datetime(2026, 9, 2, 10, tzinfo=UTC), Status.CANCELED, 40),
        (datetime(2026, 9, 2, 12, tzinfo=UTC), Status.NO_SHOW, 40),
        (datetime(2026, 9, 2, 14, tzinfo=UTC), Status.PENDING_PAYMENT, 40),
        (datetime(2026, 9, 17, 10, tzinfo=UTC), Status.BOOKED, 40),
        (datetime(2026, 8, 31, 10, tzinfo=UTC), Status.COMPLETED, 40),
    ])
    weeks = await _income()
    assert sum(w["income"] for w in weeks) == 0


async def test_weekly_income_uses_berlin_dates():
    # Sunday 23:30 UTC is Monday 01:30 in Berlin, so it lands in the next week.
    await _seed([(datetime(2026, 9, 6, 23, 30, tzinfo=UTC), Status.COMPLETED, 40)])
    weeks = await _income()
    assert weeks[1] == {"week_start": date(2026, 9, 7), "income": 40.0, "appointments": 1}


async def test_weekly_income_endpoint(client):
    response = await client.get("/api/admin/stats/weekly-income?start=2026-09-01")
    assert response.status_code == 200
    data = response.json()
    assert data[0] == {"week_start": "2026-08-31", "income": 0.0, "appointments": 0}


async def test_weekly_income_endpoint_requires_start(client):
    response = await client.get("/api/admin/stats/weekly-income")
    assert response.status_code == 422
