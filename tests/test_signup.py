from sqlalchemy import select

from database import SessionLocal
from models import Exec


def sign_up(client, **overrides):
    data = {"name": "New Exec", "email": "new@example.com", "password": "long-enough-password"}
    data.update(overrides)
    return client.post("/auth/signup", json=data)


def test_signup_creates_pending_account(client, log_in):
    response = sign_up(client)

    assert response.status_code == 201
    assert log_in(email="new@example.com", password="long-enough-password").status_code == 403


def test_signup_cannot_choose_admin_role(client):
    sign_up(client, role="admin")

    with SessionLocal() as db:
        new_exec = db.scalar(select(Exec).where(Exec.email == "new@example.com"))

    assert new_exec.role == "exec"
    assert new_exec.approved_at is None


def test_signup_rejects_duplicate_email_any_case(client):
    sign_up(client)

    response = sign_up(client, email="NEW@Example.com")

    assert response.status_code == 409


def test_signup_rejects_short_password(client):
    response = sign_up(client, password="short")

    assert response.status_code == 422


def test_signup_rejects_invalid_email(client):
    response = sign_up(client, email="notanemail")

    assert response.status_code == 422