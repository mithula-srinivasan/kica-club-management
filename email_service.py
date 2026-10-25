import os
import smtplib
from email.message import EmailMessage

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(to: str, subject: str, text: str) -> None:
    # Without Gmail settings (e.g. on your Mac), print the email instead of sending it
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print(f"\n--- EMAIL to {to} ---\nSubject: {subject}\n\n{text}\n--- END EMAIL ---\n")
        return

    message = EmailMessage()
    message["From"] = f"KICA Chess Club <{GMAIL_ADDRESS}>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(message)