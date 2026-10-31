from fastapi.testclient import TestClient

from app import app
from sqlalchemy import select

from database import SessionLocal
from models import AuditLog


def test_regular_exec_cannot_use_admin_endpoints(client, make_exec, log_in):
    make_exec()
    log_in()

    assert client.get("/execs/pending").status_code == 403


def test_admin_sees_only_pending_signups(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    make_exec(email="approved@example.com")
    make_exec(email="pending@example.com", approved=False)
    log_in(email="admin@example.com")

    response = client.get("/execs/pending")

    assert response.status_code == 200
    assert [e["email"] for e in response.json()] == ["pending@example.com"]


def test_approved_signup_can_log_in(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    pending = make_exec(email="pending@example.com", approved=False)
    log_in(email="admin@example.com")

    assert client.post(f"/execs/{pending.exec_id}/approve").status_code == 200

    client.post("/auth/logout")
    assert log_in(email="pending@example.com").status_code == 200


def test_reject_removes_pending_signup(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    pending = make_exec(email="pending@example.com", approved=False)
    log_in(email="admin@example.com")

    assert client.delete(f"/execs/{pending.exec_id}").status_code == 204
    assert client.get("/execs/pending").json() == []


def test_cannot_reject_approved_exec(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    approved = make_exec(email="approved@example.com")
    log_in(email="admin@example.com")

    assert client.delete(f"/execs/{approved.exec_id}").status_code == 409


def test_make_admin_and_remove_admin(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    other = make_exec(email="other@example.com")
    log_in(email="admin@example.com")

    assert client.post(f"/execs/{other.exec_id}/make-admin").json()["role"] == "admin"
    assert client.post(f"/execs/{other.exec_id}/remove-admin").json()["role"] == "exec"


def test_cannot_remove_last_admin(client, make_exec, log_in):
    admin = make_exec(email="admin@example.com", role="admin")
    log_in(email="admin@example.com")

    assert client.post(f"/execs/{admin.exec_id}/remove-admin").status_code == 409


def test_admin_cannot_deactivate_self(client, make_exec, log_in):
    admin = make_exec(email="admin@example.com", role="admin")
    log_in(email="admin@example.com")

    assert client.post(f"/execs/{admin.exec_id}/deactivate").status_code == 409


def test_deactivating_logs_exec_out_everywhere(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    member = make_exec(email="member@example.com")

    # A second "browser" for the member, so both can be logged in at once
    member_client = TestClient(app)
    member_client.post(
        "/auth/login",
        json={"email": "member@example.com", "password": "correct-password"}
    )
    assert member_client.get("/players/").status_code == 200

    log_in(email="admin@example.com")
    client.post(f"/execs/{member.exec_id}/deactivate")

    assert member_client.get("/players/").status_code == 401


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


def test_approving_is_recorded_in_audit_log(client, make_exec, log_in):
    admin = make_exec(email="admin@example.com", role="admin")
    pending = make_exec(email="pending@example.com", approved=False)
    log_in(email="admin@example.com")

    client.post(f"/execs/{pending.exec_id}/approve")

    [entry] = audit_entries()
    assert entry.exec_id == admin.exec_id
    assert entry.action == "UPDATE"
    assert entry.record_id == pending.exec_id
    assert entry.old_values == {"approved_at": None}


def test_rejecting_keeps_name_in_audit_log(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    pending = make_exec(email="pending@example.com", name="Ahmed", approved=False)
    log_in(email="admin@example.com")

    client.delete(f"/execs/{pending.exec_id}")

    [entry] = audit_entries()
    assert entry.action == "DELETE"
    assert entry.old_values == {"name": "Ahmed", "email": "pending@example.com"}


def test_failed_action_leaves_no_audit_entry(client, make_exec, log_in):
    admin = make_exec(email="admin@example.com", role="admin")
    log_in(email="admin@example.com")

    client.post(f"/execs/{admin.exec_id}/remove-admin")

    assert audit_entries() == []


def test_list_execs_shows_approved_including_inactive(client, make_exec, log_in):
    make_exec(email="admin@example.com", name="Admin", role="admin")
    make_exec(email="former@example.com", name="Former", is_active=False)
    make_exec(email="pending@example.com", name="Pending", approved=False)
    log_in(email="admin@example.com")

    execs = client.get("/execs/").json()

    assert [e["name"] for e in execs] == ["Admin", "Former"]
    assert execs[1]["is_active"] is False
    assert "password_hash" not in execs[0]