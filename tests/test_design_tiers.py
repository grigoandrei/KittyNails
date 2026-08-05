import pytest


async def test_create_design_tier(client):
    response = await client.post("/api/admin/design-tiers", json={
        "name": "Simple",
        "duration_minutes": 15,
        "price": 10.00,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Simple"
    assert data["duration_minutes"] == 15
    assert data["price"] == 10.00
    assert data["is_active"] is True
    assert data["sort_order"] == 0
    assert "id" in data


async def test_create_design_tier_with_sort_order(client):
    response = await client.post("/api/admin/design-tiers", json={
        "name": "Advanced",
        "duration_minutes": 90,
        "price": 45.00,
        "sort_order": 3,
    })
    assert response.status_code == 201
    assert response.json()["sort_order"] == 3


async def test_create_duplicate_design_tier(client):
    await client.post("/api/admin/design-tiers", json={
        "name": "Simple",
        "duration_minutes": 15,
        "price": 10.00,
    })
    response = await client.post("/api/admin/design-tiers", json={
        "name": "Simple",
        "duration_minutes": 20,
        "price": 12.00,
    })
    assert response.status_code == 409


async def test_update_design_tier(client):
    create_resp = await client.post("/api/admin/design-tiers", json={
        "name": "Medium",
        "duration_minutes": 45,
        "price": 25.00,
    })
    design_tier_id = create_resp.json()["id"]

    update_resp = await client.put(f"/api/admin/design-tiers/{design_tier_id}", json={
        "price": 30.00,
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == 30.00
    assert update_resp.json()["name"] == "Medium"  # unchanged


async def test_update_nonexistent_design_tier(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.put(f"/api/admin/design-tiers/{fake_id}", json={
        "price": 50.00,
    })
    assert response.status_code == 404


async def test_get_all_design_tiers(client):
    await client.post("/api/admin/design-tiers", json={
        "name": "Simple",
        "duration_minutes": 15,
        "price": 10.00,
    })
    await client.post("/api/admin/design-tiers", json={
        "name": "Advanced",
        "duration_minutes": 90,
        "price": 45.00,
    })
    response = await client.get("/api/admin/design-tiers")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_active_design_tiers_excludes_inactive(client):
    create_resp = await client.post("/api/admin/design-tiers", json={
        "name": "Old Tier",
        "duration_minutes": 15,
        "price": 8.00,
    })
    design_tier_id = create_resp.json()["id"]
    await client.put(f"/api/admin/design-tiers/{design_tier_id}", json={
        "is_active": False,
    })

    await client.post("/api/admin/design-tiers", json={
        "name": "Active Tier",
        "duration_minutes": 45,
        "price": 25.00,
    })

    response = await client.get("/api/design-tiers")
    assert response.status_code == 200
    tiers = response.json()
    assert len(tiers) == 1
    assert tiers[0]["name"] == "Active Tier"


async def test_get_active_design_tiers_ordered_by_sort_order(client):
    await client.post("/api/admin/design-tiers", json={
        "name": "Third", "duration_minutes": 15, "price": 10.00, "sort_order": 3,
    })
    await client.post("/api/admin/design-tiers", json={
        "name": "First", "duration_minutes": 15, "price": 10.00, "sort_order": 1,
    })
    await client.post("/api/admin/design-tiers", json={
        "name": "Second", "duration_minutes": 15, "price": 10.00, "sort_order": 2,
    })

    response = await client.get("/api/design-tiers")
    assert response.status_code == 200
    names = [dt["name"] for dt in response.json()]
    assert names == ["First", "Second", "Third"]
