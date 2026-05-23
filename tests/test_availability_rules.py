import pytest


async def test_create_availability_rule(client):
    response = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 1,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["day_of_week"] == 1
    assert data["start_time"] == "09:00:00"
    assert data["end_time"] == "17:00:00"
    assert "id" in data


async def test_create_rule_invalid_time_order(client):
    response = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 1,
        "start_time": "17:00:00",
        "end_time": "09:00:00",
    })
    assert response.status_code == 400


async def test_create_rule_invalid_day_of_week(client):
    response = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 7,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
    })
    assert response.status_code == 400


async def test_get_all_availability_rules(client):
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "12:00:00",
    })
    await client.post("/api/admin/availability-rules", json={
        "day_of_week": 0,
        "start_time": "13:00:00",
        "end_time": "17:00:00",
    })
    response = await client.get("/api/admin/availability-rules")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_update_availability_rule(client):
    create_resp = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 2,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
    })
    rule_id = create_resp.json()["id"]

    update_resp = await client.put(f"/api/admin/availability-rules/{rule_id}", json={
        "end_time": "18:00:00",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["end_time"] == "18:00:00"
    assert update_resp.json()["start_time"] == "09:00:00"  # unchanged


async def test_update_nonexistent_rule(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.put(f"/api/admin/availability-rules/{fake_id}", json={
        "end_time": "18:00:00",
    })
    assert response.status_code == 404


async def test_update_rule_invalid_time_order(client):
    create_resp = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 3,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
    })
    rule_id = create_resp.json()["id"]

    response = await client.put(f"/api/admin/availability-rules/{rule_id}", json={
        "start_time": "18:00:00",
    })
    assert response.status_code == 400


async def test_delete_availability_rule(client):
    create_resp = await client.post("/api/admin/availability-rules", json={
        "day_of_week": 4,
        "start_time": "10:00:00",
        "end_time": "15:00:00",
    })
    rule_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/admin/availability-rules/{rule_id}")
    assert delete_resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get("/api/admin/availability-rules")
    assert len(get_resp.json()) == 0


async def test_delete_nonexistent_rule(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/api/admin/availability-rules/{fake_id}")
    assert response.status_code == 404
