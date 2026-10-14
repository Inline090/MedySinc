"""Sends verification codes by email over SMTP."""

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.exceptions import AppError


def send_verification_code(to_email: str, code: str) -> None:
    """Emails a one time code to the given address."""

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise AppError("Email sending is not configured", 503)

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = "Your MedSync verification code"
    message.set_content(
        "Your MedSync verification code is "
        f"{code}.\n\nIt expires in {settings.VERIFICATION_CODE_TTL_MINUTES} minutes."
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
