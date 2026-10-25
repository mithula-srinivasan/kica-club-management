import os

import httpx

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "KICA <no-reply@example.com>")


def send_email(to: str, subject: str, text: str) -> None:
    # Without an API key (e.g. on your Mac), print the email instead of sending it
    if not RESEND_API_KEY:
        print(f"\n--- EMAIL to {to} ---\nSubject: {subject}\n\n{text}\n--- END EMAIL ---\n")
        return

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json={
            "from": EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "text": text
        },
        timeout=10
    )
    response.raise_for_status()