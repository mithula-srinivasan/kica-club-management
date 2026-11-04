import pytest

import config
from database import sqlalchemy_url


def test_render_database_url_is_converted():
    assert sqlalchemy_url("postgresql://user:pw@host/db") == "postgresql+psycopg://user:pw@host/db"
    assert sqlalchemy_url("postgres://user:pw@host/db") == "postgresql+psycopg://user:pw@host/db"
    assert sqlalchemy_url("postgresql+psycopg:///kica_test") == "postgresql+psycopg:///kica_test"


def test_missing_setting_uses_default_on_mac(monkeypatch):
    monkeypatch.delenv("SOME_SETTING", raising=False)

    assert config.setting("SOME_SETTING", "fallback") == "fallback"


def test_missing_setting_stops_production(monkeypatch):
    monkeypatch.delenv("SOME_SETTING", raising=False)
    monkeypatch.setattr(config, "IS_PRODUCTION", True)

    with pytest.raises(RuntimeError, match="SOME_SETTING"):
        config.setting("SOME_SETTING", "fallback")


def test_security_headers_are_sent(client):
    response = client.get("/auth/me")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"