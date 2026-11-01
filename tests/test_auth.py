from httpx import ASGITransport, AsyncClient

from src.auth import create_access_token, get_current_admin
from src.config import settings
from src.main import app


async def test_login_success(client):
    response = await client.post("/api/admin/login", json={
        "username": "admin",
        "password": "testpass",
    })
    assert response.status_code == 200
    assert response.json()["access_token"]


async def test_login_wrong_password(client):
    response = await client.post("/api/admin/login", json={
        "username": "admin",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


async def test_login_malformed_hash_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD_HASH", "$2b$12$placeholder")
    response = await client.post("/api/admin/login", json={
        "username": "admin",
        "password": "testpass",
    })
    assert response.status_code == 401


async def test_login_wrong_username(client):
    response = await client.post("/api/admin/login", json={
        "username": "notadmin",
        "password": "testpass",
    })
    assert response.status_code == 401


async def test_admin_endpoint_without_token():
    """Test that admin endpoints reject requests without auth when override is removed."""
    # Create a fresh client without the auth override
    test_app = app
    overrides = test_app.dependency_overrides.copy()
    test_app.dependency_overrides.pop(get_current_admin, None)

    try:
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/admin/nail-types")
            # HTTPBearer returns 401 "Not authenticated" when no credentials are sent.
            assert response.status_code == 401
    finally:
        # Always restore so a failed assertion here can't leak an unauthenticated
        # app into the rest of the session.
        test_app.dependency_overrides = overrides


async def test_admin_endpoint_with_valid_token():
    """Test that admin endpoints accept a valid JWT."""
    test_app = app
    overrides = test_app.dependency_overrides.copy()
    test_app.dependency_overrides.pop(get_current_admin, None)

    try:
        token = create_access_token({"sub": "admin"})
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/admin/nail-types",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
    finally:
        test_app.dependency_overrides = overrides


async def test_admin_endpoint_with_invalid_token():
    """Test that admin endpoints reject an invalid JWT."""
    test_app = app
    overrides = test_app.dependency_overrides.copy()
    test_app.dependency_overrides.pop(get_current_admin, None)

    try:
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(
                "/api/admin/nail-types",
                headers={"Authorization": "Bearer invalid.token.here"},
            )
            assert response.status_code == 401
    finally:
        test_app.dependency_overrides = overrides
