from datetime import timedelta

import pytest
from sqlalchemy import update

from database import SessionLocal
from models import RateLimitHit


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []

    def fake_send_email(to, subject, text):
        emails.append({"to": to, "subject": subject, "text": text})

    # Capture emails instead of sending them
    monkeypatch.setattr("routers.auth.send_email", fake_send_email)

    return emails


def log_in(client, password="correct-password", email="exec@example.com"):
    return client.post("/auth/login", json={"email": email, "password": password})


def make_hits_older(minutes):
    """Pretend the recorded attempts happened this many minutes earlier."""
    with SessionLocal() as db:
        db.execute(
            update(RateLimitHit).values(
                created_at=RateLimitHit.created_at - timedelta(minutes=minutes)
            )
        )
        db.commit()


def test_five_wrong_passwords_block_the_email(client, make_exec):
    make_exec()

    for _ in range(5):
        assert log_in(client, password="wrong-password").status_code == 401

    # Blocked now, even with the right password
    response = log_in(client)

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many attempts. Please try again in 15 minutes."


def test_block_ends_after_15_minutes(client, make_exec):
    make_exec()

    for _ in range(5):
        log_in(client, password="wrong-password")

    make_hits_older(minutes=16)

    assert log_in(client).status_code == 200


def test_correct_password_clears_the_count(client, make_exec):
    make_exec()

    for _ in range(4):
        log_in(client, password="wrong-password")
    assert log_in(client).status_code == 200

    # Counting starts again from zero
    for _ in range(4):
        log_in(client, password="wrong-password")
    assert log_in(client).status_code == 200


def test_block_is_only_for_that_email(client, make_exec):
    make_exec()
    make_exec(email="other@example.com", name="Other Exec")

    for _ in range(5):
        log_in(client, password="wrong-password")

    assert log_in(client).status_code == 429
    assert log_in(client, email="other@example.com").status_code == 200


def test_too_many_wrong_attempts_from_one_ip(client, make_exec):
    make_exec()

    # 20 failures, each for a different email, all from the same IP
    for number in range(20):
        log_in(client, email=f"guess{number}@example.com", password="wrong-password")

    assert log_in(client).status_code == 429


def test_password_reset_clears_the_block(client, make_exec, sent_emails):
    make_exec()

    for _ in range(5):
        log_in(client, password="wrong-password")
    assert log_in(client).status_code == 429

    client.post("/auth/forgot-password", json={"email": "exec@example.com"})
    token = sent_emails[0]["text"].split("#token=")[1].split()[0]
    client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "brand-new-password"}
    )

    assert log_in(client, password="brand-new-password").status_code == 200


def test_forgot_password_is_limited(client, make_exec, sent_emails):
    make_exec()

    for _ in range(3):
        assert client.post(
            "/auth/forgot-password", json={"email": "exec@example.com"}
        ).status_code == 200

    response = client.post("/auth/forgot-password", json={"email": "exec@example.com"})

    assert response.status_code == 429
    assert len(sent_emails) == 3


def test_signup_is_limited_per_ip(client):
    for number in range(5):
        response = client.post(
            "/auth/signup",
            json={
                "name": f"Person {number}",
                "email": f"person{number}@example.com",
                "password": "a-long-enough-password",
            },
        )
        assert response.status_code == 201

    response = client.post(
        "/auth/signup",
        json={
            "name": "One Too Many",
            "email": "toomany@example.com",
            "password": "a-long-enough-password",
        },
    )

    assert response.status_code == 429