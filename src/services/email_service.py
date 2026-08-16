"""Email service for sending confirmation and reminder emails via AWS SES."""

import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from src.config import settings

logger = logging.getLogger(__name__)


def _get_ses_client():
    return boto3.client("ses", region_name=settings.SES_REGION)


def _format_datetime_berlin(dt: datetime) -> str:
    """Format a datetime for display in Berlin timezone (CET/CEST)."""
    from zoneinfo import ZoneInfo

    berlin_tz = ZoneInfo("Europe/Berlin")
    local_dt = dt.astimezone(berlin_tz)
    return local_dt.strftime("%A, %B %d, %Y at %H:%M")


def _base_html(title: str, content: str) -> str:
    """Wrap email content in a styled HTML shell."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin:0; padding:0; background-color:#fdf2f8; font-family:'Helvetica Neue',Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#fdf2f8;">
        <tr>
            <td align="center" style="padding:40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0"
                       style="background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color:#be185d; padding:30px; text-align:center;">
                            <h1 style="margin:0; color:#ffffff; font-size:28px; font-weight:700;">
                                💅 {settings.STUDIO_NAME}
                            </h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding:40px 30px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color:#fce7f3; padding:25px 30px; text-align:center; border-top:1px solid #f9a8d4;">
                            <p style="margin:0 0 8px; color:#9d174d; font-size:14px;">
                                📍 {settings.STUDIO_ADDRESS}
                            </p>
                            <p style="margin:0; font-size:13px;">
                                <a href="{settings.STUDIO_INSTAGRAM}" style="color:#be185d; text-decoration:none;">
                                    Follow us on Instagram @kittynails_berlin
                                </a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def _confirmation_html(
    client_email: str,
    start_time: datetime,
    end_time: datetime,
    nail_type_name: str,
    design_tier_name: str | None,
    quoted_price: float,
) -> str:
    """Build the confirmation email HTML body."""
    formatted_start = _format_datetime_berlin(start_time)
    formatted_end_time = _format_datetime_berlin(end_time).split(" at ")[1]

    service_line = nail_type_name
    if design_tier_name:
        service_line += f" — {design_tier_name} design"

    content = f"""\
<h2 style="margin:0 0 20px; color:#1f2937; font-size:22px;">Booking Confirmed! ✨</h2>
<p style="color:#4b5563; font-size:16px; line-height:1.6; margin:0 0 25px;">
    Hi there! Your nail appointment has been confirmed. Here are the details:
</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"
       style="background-color:#fdf2f8; border-radius:8px; padding:20px; margin-bottom:25px;">
    <tr>
        <td style="padding:12px 20px; border-bottom:1px solid #fce7f3;">
            <strong style="color:#9d174d;">📅 Date & Time</strong><br>
            <span style="color:#374151;">{formatted_start} – {formatted_end_time}</span>
        </td>
    </tr>
    <tr>
        <td style="padding:12px 20px; border-bottom:1px solid #fce7f3;">
            <strong style="color:#9d174d;">💅 Service</strong><br>
            <span style="color:#374151;">{service_line}</span>
        </td>
    </tr>
    <tr>
        <td style="padding:12px 20px;">
            <strong style="color:#9d174d;">💰 Price</strong><br>
            <span style="color:#374151;">€{quoted_price:.2f}</span>
        </td>
    </tr>
</table>
<p style="color:#4b5563; font-size:14px; line-height:1.6; margin:0 0 10px;">
    <strong>Please note:</strong> If you need to cancel or reschedule, please contact us
    at least 24 hours before your appointment via Instagram DM.
</p>
<p style="color:#6b7280; font-size:13px; margin:0;">
    See you soon! 🐱
</p>"""

    return _base_html("Appointment Confirmed", content)


def _reminder_html(
    client_email: str,
    start_time: datetime,
    nail_type_name: str,
    design_tier_name: str | None,
) -> str:
    """Build the reminder email HTML body (sent 24h before appointment)."""
    formatted_start = _format_datetime_berlin(start_time)

    service_line = nail_type_name
    if design_tier_name:
        service_line += f" — {design_tier_name} design"

    content = f"""\
<h2 style="margin:0 0 20px; color:#1f2937; font-size:22px;">Reminder: Your Appointment is Tomorrow! 🐱</h2>
<p style="color:#4b5563; font-size:16px; line-height:1.6; margin:0 0 25px;">
    Just a friendly reminder that you have a nail appointment coming up:
</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"
       style="background-color:#fdf2f8; border-radius:8px; padding:20px; margin-bottom:25px;">
    <tr>
        <td style="padding:12px 20px; border-bottom:1px solid #fce7f3;">
            <strong style="color:#9d174d;">📅 When</strong><br>
            <span style="color:#374151;">{formatted_start}</span>
        </td>
    </tr>
    <tr>
        <td style="padding:12px 20px;">
            <strong style="color:#9d174d;">💅 Service</strong><br>
            <span style="color:#374151;">{service_line}</span>
        </td>
    </tr>
</table>
<p style="color:#4b5563; font-size:14px; line-height:1.6; margin:0 0 10px;">
    📍 <strong>Address:</strong> {settings.STUDIO_ADDRESS}
</p>
<p style="color:#4b5563; font-size:14px; line-height:1.6; margin:0 0 10px;">
    If you can no longer make it, please let us know as soon as possible via Instagram DM.
</p>
<p style="color:#6b7280; font-size:13px; margin:0;">
    Looking forward to seeing you! ✨
</p>"""

    return _base_html("Appointment Reminder", content)


async def send_confirmation_email(
    client_email: str,
    start_time: datetime,
    end_time: datetime,
    nail_type_name: str,
    design_tier_name: str | None,
    quoted_price: float,
) -> bool:
    """Send a booking confirmation email. Returns True on success, False on failure."""
    if not settings.SES_ENABLED:
        logger.info("SES disabled — skipping confirmation email to %s", client_email)
        return False

    html_body = _confirmation_html(
        client_email=client_email,
        start_time=start_time,
        end_time=end_time,
        nail_type_name=nail_type_name,
        design_tier_name=design_tier_name,
        quoted_price=quoted_price,
    )

    subject = f"Appointment Confirmed — {_format_datetime_berlin(start_time)}"

    return _send_email(client_email, subject, html_body)


async def send_reminder_email(
    client_email: str,
    start_time: datetime,
    nail_type_name: str,
    design_tier_name: str | None,
) -> bool:
    """Send an appointment reminder email (24h before). Returns True on success."""
    if not settings.SES_ENABLED:
        logger.info("SES disabled — skipping reminder email to %s", client_email)
        return False

    html_body = _reminder_html(
        client_email=client_email,
        start_time=start_time,
        nail_type_name=nail_type_name,
        design_tier_name=design_tier_name,
    )

    subject = f"Reminder: Your nail appointment is tomorrow! — {settings.STUDIO_NAME}"

    return _send_email(client_email, subject, html_body)


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Low-level SES send. Returns True on success, False on failure."""
    try:
        client = _get_ses_client()
        client.send_email(
            Source=settings.SES_SENDER_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except ClientError as e:
        logger.error(
            "Failed to send email to %s: %s",
            to_email,
            e.response["Error"]["Message"],
        )
        return False
    except Exception as e:  # noqa: BLE001
        logger.error("Unexpected error sending email to %s: %s", to_email, str(e))
        return False
