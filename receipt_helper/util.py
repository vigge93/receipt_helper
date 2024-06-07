import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(recipient, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = current_app.config["RECEIPTS_EMAIL_SENDER"]
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL(current_app.config["RECEIPTS_SMTP_HOST"]) as s:
            s.login(
                current_app.config["RECEIPTS_SMTP_USERNAME"],
                current_app.config["RECEIPTS_SMTP_PASSWORD"],
            )
            s.send_message(msg)
    except smtplib.SMTPException as ex:
        current_app.logger.error(f"Failed to send email: {type(ex).__name__}: {ex}")
        raise