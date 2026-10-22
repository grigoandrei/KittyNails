"""Telegram notifications for the artist.

Outbound-only: posts messages to the Telegram Bot API. Used by the 08:00
daily overview and by the new-booking notification.

Fault-tolerant by design — a Telegram or network failure must never break a
scheduled job. Returns True on success, False otherwise; never raises.
"""

import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"
_TIMEOUT_SECONDS = 10

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def format_appointment_line(
    start_time: datetime,
    nail_type_name: str,
    design_tier_name: str | None,
    needs_removal: bool,
    quoted_price: float,
    client_email: str,
) -> str:
    """One appointment as a Telegram HTML line. Text is escaped because the
    message is sent with parse_mode=HTML."""
    local = start_time.astimezone(BERLIN_TZ)
    service = nail_type_name
    if design_tier_name:
        service += f" — {design_tier_name}"
    if needs_removal:
        service += " (+ removal)"
    return (
        f"🕐 <b>{local.strftime('%H:%M')}</b> — {html.escape(service)}\n"
        f"   €{quoted_price:.2f} · {html.escape(client_email)}"
    )


async def send_message(text: str) -> bool:
    """Send a message to the configured Telegram chat.

    Returns False (without raising) if Telegram is disabled, not configured,
    or the request fails.
    """
    if not settings.TELEGRAM_ENABLED:
        logger.info("Telegram disabled — skipping message")
        return False

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram enabled but token/chat_id not configured")
        return False

    url = f"{_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
        if response.status_code != 200:
            logger.error(
                "Telegram sendMessage failed: HTTP %s — %s",
                response.status_code,
                response.text[:300],
            )
            return False
        return True
    except Exception as e:  # noqa: BLE001 — never let a notification break a job
        logger.error("Telegram sendMessage error: %s", e)
        return False
