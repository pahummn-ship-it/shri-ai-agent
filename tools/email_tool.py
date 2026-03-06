from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config.settings import get_settings


class EmailTool:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_email(self, to: str, subject: str, body: str) -> dict[str, str]:
        if not (self.settings.smtp_host and self.settings.smtp_username and self.settings.smtp_password):
            return {
                "status": "skipped",
                "message": "SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD.",
            }

        msg = EmailMessage()
        msg["From"] = self.settings.default_from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)

        return {"status": "sent", "message": f"Email sent to {to}."}
