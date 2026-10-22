"""Tests for the Telegram service, the 08:00 daily overview, and the
new-booking ping (no DB needed)."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from src.digest_handler import (
    BERLIN_TZ,
    _today_berlin_bounds,
    build_digest_message,
    seconds_until_next_run,
)
from src.services import telegram_service
from src.services.booking_notifier import build_new_booking_message

UTC = ZoneInfo("UTC")


class TestTodayBounds:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    def test_bounds_are_current_berlin_day(self):
        now = datetime(2026, 6, 15, 8, 0, tzinfo=BERLIN_TZ)
        start, end, target = _today_berlin_bounds(now)
        assert target.isoformat() == "2026-06-15"
        assert start == datetime(2026, 6, 15, 0, 0, tzinfo=BERLIN_TZ)
        assert end == datetime(2026, 6, 16, 0, 0, tzinfo=BERLIN_TZ)

    def test_bounds_from_utc_input(self):
        # 23:30 UTC on Jun 15 = 01:30 Berlin Jun 16 (CEST), so "today" = Jun 16.
        now = datetime(2026, 6, 15, 23, 30, tzinfo=UTC)
        _, _, target = _today_berlin_bounds(now)
        assert target.isoformat() == "2026-06-16"


class TestSecondsUntilNextRun:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    def test_later_today(self):
        now = datetime(2026, 6, 15, 7, 0, tzinfo=BERLIN_TZ)  # 07:00, target 08:00
        assert seconds_until_next_run(now) == 3600

    def test_rolls_to_tomorrow_when_past(self):
        now = datetime(2026, 6, 15, 8, 30, tzinfo=BERLIN_TZ)  # past 08:00
        secs = seconds_until_next_run(now)
        # next 08:00 is tomorrow → 23.5h
        assert secs == pytest.approx(23.5 * 3600)

    def test_dst_safe_uses_berlin_wall_clock(self):
        # Winter (CET, UTC+1): at 07:00 Berlin, still exactly 1h to 08:00.
        now = datetime(2026, 1, 15, 7, 0, tzinfo=BERLIN_TZ)
        assert seconds_until_next_run(now) == 3600


class TestBuildDigestMessage:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    def test_empty_case(self):
        target = datetime(2026, 6, 16, tzinfo=BERLIN_TZ).date()
        msg = build_digest_message([], target)
        assert "No appointments today" in msg

    def test_lists_appointments_in_berlin_time(self):
        target = datetime(2026, 6, 16, tzinfo=BERLIN_TZ).date()
        appts = [
            {
                # 08:00 UTC = 10:00 Berlin (CEST)
                "start_time": datetime(2026, 6, 16, 8, 0, tzinfo=UTC),
                "nail_type_name": "Regular",
                "design_tier_name": "Medium",
                "needs_removal": True,
                "quoted_price": 65.0,
                "client_email": "a@example.com",
            }
        ]
        msg = build_digest_message(appts, target)
        assert "10:00" in msg
        assert "Regular — Medium" in msg
        assert "(+ removal)" in msg
        assert "€65.00" in msg
        assert "a@example.com" in msg
        assert "1 appointment" in msg

    def test_no_design_tier_no_removal(self):
        target = datetime(2026, 6, 16, tzinfo=BERLIN_TZ).date()
        appts = [
            {
                "start_time": datetime(2026, 6, 16, 9, 0, tzinfo=BERLIN_TZ),
                "nail_type_name": "Japanese Manicure",
                "design_tier_name": None,
                "needs_removal": False,
                "quoted_price": 30.0,
                "client_email": "b@example.com",
            }
        ]
        msg = build_digest_message(appts, target)
        assert "Japanese Manicure" in msg
        assert "—" not in msg.split("Japanese Manicure")[1].split("\n")[0]
        assert "removal" not in msg


class TestSendMessage:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    @patch("src.services.telegram_service.settings")
    async def test_disabled_returns_false(self, mock_settings):
        mock_settings.TELEGRAM_ENABLED = False
        assert await telegram_service.send_message("hi") is False

    @patch("src.services.telegram_service.settings")
    async def test_missing_config_returns_false(self, mock_settings):
        mock_settings.TELEGRAM_ENABLED = True
        mock_settings.TELEGRAM_BOT_TOKEN = ""
        mock_settings.TELEGRAM_CHAT_ID = ""
        assert await telegram_service.send_message("hi") is False

    @patch("src.services.telegram_service.httpx.AsyncClient")
    @patch("src.services.telegram_service.settings")
    async def test_success(self, mock_settings, mock_client_cls):
        mock_settings.TELEGRAM_ENABLED = True
        mock_settings.TELEGRAM_BOT_TOKEN = "tok"
        mock_settings.TELEGRAM_CHAT_ID = "123"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        assert await telegram_service.send_message("hi") is True
        mock_client.post.assert_awaited_once()

    @patch("src.services.telegram_service.httpx.AsyncClient")
    @patch("src.services.telegram_service.settings")
    async def test_http_error_returns_false(self, mock_settings, mock_client_cls):
        mock_settings.TELEGRAM_ENABLED = True
        mock_settings.TELEGRAM_BOT_TOKEN = "tok"
        mock_settings.TELEGRAM_CHAT_ID = "123"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "bad request"
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        assert await telegram_service.send_message("hi") is False

    @patch("src.services.telegram_service.httpx.AsyncClient")
    @patch("src.services.telegram_service.settings")
    async def test_exception_returns_false(self, mock_settings, mock_client_cls):
        mock_settings.TELEGRAM_ENABLED = True
        mock_settings.TELEGRAM_BOT_TOKEN = "tok"
        mock_settings.TELEGRAM_CHAT_ID = "123"
        mock_client_cls.side_effect = RuntimeError("network down")

        # Fault-tolerant: must not raise.
        assert await telegram_service.send_message("hi") is False


class TestNewBookingMessage:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    def _appointment(self, **overrides):
        fields = {
            # 08:00 UTC = 10:00 Berlin (CEST)
            "start_time": datetime(2026, 6, 16, 8, 0, tzinfo=UTC),
            "needs_removal": False,
            "quoted_price": 50.0,
            "client_email": "c@example.com",
            "source": "web",
        }
        fields.update(overrides)
        return SimpleNamespace(**fields)

    def test_web_booking(self):
        msg = build_new_booking_message(self._appointment(), "Regular", "Medium")
        assert "New booking" in msg
        assert "Website" in msg
        assert "Tuesday, June 16" in msg
        assert "10:00" in msg
        assert "Regular — Medium" in msg
        assert "€50.00" in msg
        assert "c@example.com" in msg

    def test_instagram_booking_with_removal(self):
        appt = self._appointment(source="instagram", needs_removal=True)
        msg = build_new_booking_message(appt, "Japanese Manicure", None)
        assert "Instagram" in msg
        assert "Japanese Manicure (+ removal)" in msg

    def test_escapes_html(self):
        msg = build_new_booking_message(self._appointment(), "Nails <b>", None)
        assert "Nails &lt;b&gt;" in msg
