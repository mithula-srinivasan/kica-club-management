import smtplib
from email.message import EmailMessage

from config import setting

# Required in production. On your Mac, if they're missing, emails are printed instead.
GMAIL_ADDRESS = setting("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = setting("GMAIL_APP_PASSWORD")


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