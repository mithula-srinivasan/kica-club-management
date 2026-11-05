import os
from datetime import datetime, timezone, date
from decimal import Decimal

# Point the app at the test database BEFORE anything imports database.py
os.environ["DATABASE_URL"] = "postgresql+psycopg:///kica_test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import app
from database import Base, SessionLocal, engine
from models import Exec, FeeRate, Player
from security import hash_password

# Safety net: refuse to run if somehow pointed at any other database
assert engine.url.database == "kica_test", "Tests must only run against kica_test"


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def empty_tables():
    yield
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)

    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    # Every test request goes to the API, e.g. "/players/" means "/api/players/"
    return TestClient(app, base_url="http://testserver/api")


@pytest.fixture
def make_exec():
    def _make_exec(
        email="exec@example.com",
        password="correct-password",
        name="Test Exec",
        role="exec",
        approved=True,
        is_active=True
    ):
        with SessionLocal() as db:
            exec_user = Exec(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
                is_active=is_active,
                approved_at=datetime.now(timezone.utc) if approved else None
            )
            db.add(exec_user)
            db.commit()
            db.refresh(exec_user)
            return exec_user

    return _make_exec


@pytest.fixture
def log_in(client):
    def _log_in(email="exec@example.com", password="correct-password", remember_me=False):
        return client.post(
            "/auth/login",
            json={"email": email, "password": password, "remember_me": remember_me}
        )

    return _log_in


@pytest.fixture
def make_player():
    def _make_player(name="Player One", kica_id="K001", is_active=True):
        with SessionLocal() as db:
            player = Player(
                name=name,
                kica_id=kica_id,
                is_active=is_active,
                phone_1="+965 5000 0000",
                email="parent@example.com",
                parent_name="Lakshmi",
                date_of_birth=date(2014, 5, 20),
                country="To be updated",
            )
            db.add(player)
            db.commit()
            db.refresh(player)
            return player

    return _make_player


@pytest.fixture(autouse=True)
def default_fee_rate():
    with SessionLocal() as db:
        db.add(FeeRate(monthly_amount=Decimal("5.000"), effective_from=date(2000, 1, 1)))
        db.commit()