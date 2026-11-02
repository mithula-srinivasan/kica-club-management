from sqlalchemy import select

from database import SessionLocal
from models import AuditLog


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


def create_session(client, session_date="2026-10-16"):
    return client.post("/sessions/", json={"session_date": session_date})


def set_attendance(client, session_id, player_ids):
    return client.put(f"/sessions/{session_id}/attendance", json={"player_ids": player_ids})


def test_sessions_require_login(client):
    assert client.get("/sessions/").status_code == 401


def test_create_session_and_reject_duplicate_date(client, make_exec, log_in):
    make_exec()
    log_in()

    assert create_session(client).status_code == 201
    assert create_session(client).status_code == 409


def test_mark_attendance(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    bob = make_player(name="Bob", kica_id="K002")
    session_id = create_session(client).json()["session_id"]

    response = set_attendance(client, session_id, [bob.player_id, alice.player_id])

    assert response.status_code == 200
    assert [p["name"] for p in response.json()["present_players"]] == ["Alice", "Bob"]
    assert client.get("/sessions/").json()[0]["present_count"] == 2


def test_correction_removes_player_and_is_logged(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    bob = make_player(name="Bob", kica_id="K002")
    session_id = create_session(client).json()["session_id"]
    set_attendance(client, session_id, [alice.player_id, bob.player_id])

    response = set_attendance(client, session_id, [alice.player_id])

    assert [p["name"] for p in response.json()["present_players"]] == ["Alice"]
    entry = audit_entries()[-1]
    assert entry.old_values == {"present_player_ids": [alice.player_id, bob.player_id]}
    assert entry.new_values == {"present_player_ids": [alice.player_id]}


def test_removed_player_can_be_added_back(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    session_id = create_session(client).json()["session_id"]
    set_attendance(client, session_id, [alice.player_id])
    set_attendance(client, session_id, [])

    response = set_attendance(client, session_id, [alice.player_id])

    assert [p["name"] for p in response.json()["present_players"]] == ["Alice"]


def test_saving_same_list_twice_logs_once(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    session_id = create_session(client).json()["session_id"]

    set_attendance(client, session_id, [alice.player_id])
    set_attendance(client, session_id, [alice.player_id])

    # One entry for creating the session, one for the attendance change
    assert len(audit_entries()) == 2


def test_unknown_player_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()
    session_id = create_session(client).json()["session_id"]

    assert set_attendance(client, session_id, [999]).status_code == 404

def test_deleting_session_removes_attendance_and_fees(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    session_id = create_session(client).json()["session_id"]
    set_attendance(client, session_id, [alice.player_id])

    response = client.delete(f"/sessions/{session_id}")

    assert response.status_code == 204
    assert client.get(f"/sessions/{session_id}").status_code == 404
    assert client.get(f"/fees/players/{alice.player_id}").json() == []

    entry = audit_entries()[-1]
    assert entry.action == "DELETE"
    assert entry.old_values == {
        "session_date": "2026-10-16",
        "present_player_ids": [alice.player_id]
    }


def test_change_session_date_moves_attendance_and_fee(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    session_id = create_session(client, "2026-09-25").json()["session_id"]
    set_attendance(client, session_id, [alice.player_id])

    response = client.patch(f"/sessions/{session_id}", json={"session_date": "2026-10-16"})

    assert response.status_code == 200
    assert response.json()["session_date"] == "2026-10-16"
    assert [p["name"] for p in response.json()["present_players"]] == ["Player One"]

    fees = client.get(f"/fees/players/{alice.player_id}").json()
    assert [fee["fee_month"] for fee in fees] == ["2026-10-01"]

    entry = audit_entries()[-1]
    assert entry.old_values == {"session_date": "2026-09-25"}
    assert entry.new_values == {"session_date": "2026-10-16"}


def test_cannot_change_to_a_date_that_already_has_a_session(client, make_exec, log_in):
    make_exec()
    log_in()
    create_session(client, "2026-10-16")
    session_id = create_session(client, "2026-10-17").json()["session_id"]

    response = client.patch(f"/sessions/{session_id}", json={"session_date": "2026-10-16"})

    assert response.status_code == 409