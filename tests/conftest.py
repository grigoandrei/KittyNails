from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.auth import get_current_admin
from src.config import settings
from src.database import Base, get_db
from src.limiter import limiter
from src.main import app

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _today() -> date:
    return datetime.now(BERLIN_TZ).date()


def future_weekday(weekday: int, min_ahead_days: int = 7) -> date:
    """Next date on `weekday` (0=Mon) at least `min_ahead_days` in the future.

    Tests hardcoded calendar dates that have since drifted into the past, which
    trips the AppointmentCreate "must be in the future" validator (422). Compute
    the date relative to today so tests stay valid over time. A week of lead time
    keeps timestamps safely ahead of "now" regardless of the run time.
    """
    start = _today() + timedelta(days=min_ahead_days)
    offset = (weekday - start.weekday()) % 7
    return start + timedelta(days=offset)


def at(target_date: date, hour: int, minute: int = 0) -> str:
    """ISO-8601 UTC timestamp string for a date at the given hour/minute."""
    return f"{target_date}T{hour:02d}:{minute:02d}:00+00:00"

# Rate limits protect the real API but make the suite non-deterministic (a
# session issues more booking/analysis POSTs than the hourly caps allow, all
# from the same test client IP). Disable enforcement for tests.
limiter.enabled = False

engine_test = create_async_engine(settings.TEST_DATABASE_URL, poolclass=NullPool)
async_session_test = async_sessionmaker(engine_test, expire_on_commit=False)


async def override_get_db():
    async with async_session_test() as session:
        yield session


def override_get_current_admin():
    return "test-admin"


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_admin] = override_get_current_admin


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop them after."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
