import pytest


async def test_create_service(client):
    response = await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 60,
        "price": 45.00,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gel Nails"
    assert data["duration_minutes"] == 60
    assert data["price"] == 45.00
    assert data["is_active"] is True
    assert "id" in data


async def test_create_duplicate_service(client):
    await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 60,
        "price": 45.00,
    })
    response = await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 30,
        "price": 25.00,
    })
    assert response.status_code == 409


async def test_update_service(client):
    create_resp = await client.post("/api/admin/services", json={
        "name": "Extensions",
        "duration_minutes": 90,
        "price": 80.00,
    })
    service_id = create_resp.json()["id"]

    update_resp = await client.put(f"/api/admin/services/{service_id}", json={
        "price": 95.00,
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["price"] == 95.00
    assert update_resp.json()["name"] == "Extensions"  # unchanged


async def test_update_nonexistent_service(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.put(f"/api/admin/services/{fake_id}", json={
        "price": 50.00,
    })
    assert response.status_code == 404


async def test_get_all_services(client):
    await client.post("/api/admin/services", json={
        "name": "Gel Nails",
        "duration_minutes": 60,
        "price": 45.00,
    })
    await client.post("/api/admin/services", json={
        "name": "Extensions",
        "duration_minutes": 90,
        "price": 80.00,
    })
    response = await client.get("/api/admin/services")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_active_services_excludes_inactive(client):
    # Create a service then deactivate it
    create_resp = await client.post("/api/admin/services", json={
        "name": "Old Service",
        "duration_minutes": 30,
        "price": 20.00,
    })
    service_id = create_resp.json()["id"]
    await client.put(f"/api/admin/services/{service_id}", json={
        "is_active": False,
    })

    # Create an active service
    await client.post("/api/admin/services", json={
        "name": "Active Service",
        "duration_minutes": 60,
        "price": 50.00,
    })

    # Public endpoint should only show active
    response = await client.get("/api/services")
    assert response.status_code == 200
    services = response.json()
    assert len(services) == 1
    assert services[0]["name"] == "Active Service"
