from datetime import timedelta

import pytest

from src.config import settings
from src.services.pricing import round_promo_price
from tests.conftest import at, future_weekday

# The promo window is moved to a future week so these tests don't rot once the
# real Halloween window has passed.
MONDAY = future_weekday(0)
NEXT_MONDAY = MONDAY + timedelta(days=7)


@pytest.fixture(autouse=True)
def promo_window(monkeypatch):
    monkeypatch.setattr(settings, "PROMO_PERCENT", 15.0)
    monkeypatch.setattr(settings, "PROMO_START", MONDAY)
    monkeypatch.setattr(settings, "PROMO_END", MONDAY + timedelta(days=6))
    monkeypatch.setattr(settings, "PROMO_DESIGN_TIERS", ["Medium", "Advanced"])


async def setup(client, tier_name):
    """Nail type €40 + design tier €10, open Mondays. Returns the ids."""
    nail = await client.post("/api/admin/nail-types", json={
        "name": "Regular", "duration_minutes": 60, "price": 40.00,
    })
    tier = await client.post("/api/admin/design-tiers", json={
        "name": tier_name, "duration_minutes": 0, "price": 10.00,
    })
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00",
    })
    return nail.json()["id"], tier.json()["id"]


async def book(client, nail_type_id, design_tier_id, day, needs_removal=False):
    return await client.post("/api/appointments", json={
        "nail_type_id": nail_type_id,
        "design_tier_id": design_tier_id,
        "client_email": "test@example.com",
        "start_time": at(day, 10),
        "needs_removal": needs_removal,
    })


@pytest.mark.parametrize("tier_name", ["Medium", "Advanced"])
async def test_promo_tier_in_window_gets_discount(client, tier_name):
    nail_type_id, design_tier_id = await setup(client, tier_name)
    response = await book(client, nail_type_id, design_tier_id, MONDAY)
    assert response.status_code == 201
    # (40 + 10) * 0.85
    assert response.json()["quoted_price"] == 42.50


async def test_removal_fee_is_not_discounted(client):
    nail_type_id, design_tier_id = await setup(client, "Medium")
    response = await book(client, nail_type_id, design_tier_id, MONDAY, needs_removal=True)
    assert response.json()["quoted_price"] == 42.50 + 15.00


async def test_simple_tier_gets_no_discount(client):
    nail_type_id, design_tier_id = await setup(client, "Simple")
    response = await book(client, nail_type_id, design_tier_id, MONDAY)
    assert response.json()["quoted_price"] == 50.00


async def test_appointment_outside_window_gets_no_discount(client):
    nail_type_id, design_tier_id = await setup(client, "Medium")
    response = await book(client, nail_type_id, design_tier_id, NEXT_MONDAY)
    assert response.json()["quoted_price"] == 50.00


async def test_no_design_tier_gets_no_discount(client):
    nail_type_id, _ = await setup(client, "Medium")
    response = await book(client, nail_type_id, None, MONDAY)
    assert response.json()["quoted_price"] == 40.00


async def test_promo_off_when_percent_zero(client, monkeypatch):
    monkeypatch.setattr(settings, "PROMO_PERCENT", 0.0)
    nail_type_id, design_tier_id = await setup(client, "Medium")
    response = await book(client, nail_type_id, design_tier_id, MONDAY)
    assert response.json()["quoted_price"] == 50.00


async def test_admin_move_out_of_window_drops_discount(client):
    nail_type_id, design_tier_id = await setup(client, "Medium")
    appointment = (await book(client, nail_type_id, design_tier_id, MONDAY)).json()
    assert appointment["quoted_price"] == 42.50

    response = await client.patch(
        f"/api/admin/appointments/{appointment['id']}",
        json={"start_time": at(NEXT_MONDAY, 10)},
    )
    assert response.status_code == 200
    assert response.json()["quoted_price"] == 50.00


async def test_get_promotion(client):
    response = await client.get("/api/promotion")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Halloween",
        "percent": 15.0,
        "start": str(MONDAY),
        "end": str(MONDAY + timedelta(days=6)),
        "design_tiers": ["Medium", "Advanced"],
    }


async def test_get_promotion_null_when_off(client, monkeypatch):
    monkeypatch.setattr(settings, "PROMO_PERCENT", 0.0)
    response = await client.get("/api/promotion")
    assert response.json() is None


async def test_get_promotion_null_after_window(client, monkeypatch):
    monkeypatch.setattr(settings, "PROMO_END", MONDAY - timedelta(days=30))
    response = await client.get("/api/promotion")
    assert response.json() is None


@pytest.mark.parametrize("raw, expected", [
    (55.25, 55.00),  # below .50 rounds down
    (63.75, 64.00),  # above .50 rounds up
    (42.50, 42.50),  # exactly .50 stays
    (51.00, 51.00),
    (55.49, 55.00),
    (55.51, 56.00),
])
def test_round_promo_price(raw, expected):
    assert round_promo_price(raw) == expected


async def test_promo_price_is_rounded(client):
    """Extensions €55 + Medium €10 = €65, 15% off = €55.25, rounds to €55."""
    nail = await client.post("/api/admin/nail-types", json={
        "name": "Extensions", "duration_minutes": 150, "price": 55.00,
    })
    tier = await client.post("/api/admin/design-tiers", json={
        "name": "Medium", "duration_minutes": 0, "price": 10.00,
    })
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0, "start_time": "09:00:00", "end_time": "18:00:00",
    })
    response = await book(client, nail.json()["id"], tier.json()["id"], MONDAY)
    assert response.json()["quoted_price"] == 55.00
