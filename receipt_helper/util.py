import smtplib
from email.message import EmailMessage
from typing import Sequence

from flask import current_app


def send_email(recipients: str | Sequence[str], subject: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = current_app.config["RECEIPTS_EMAIL_SENDER"]

    try:
        with smtplib.SMTP_SSL(current_app.config["RECEIPTS_SMTP_HOST"]) as s:
            s.login(
                current_app.config["RECEIPTS_SMTP_USERNAME"],
                current_app.config["RECEIPTS_SMTP_PASSWORD"],
            )
            s.send_message(msg, to_addrs=recipients)
    except smtplib.SMTPException as ex:
        current_app.logger.error(f"Failed to send email: {type(ex).__name__}: {ex}")
        raise
