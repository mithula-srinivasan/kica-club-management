from sqlalchemy import select

from database import SessionLocal
from models import AuditLog


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


def create_player(client, kica_id="K001", name="Player One"):
    return client.post(
        "/players/",
        json={"kica_id": kica_id, "name": name, "joined_on": "2026-01-10"}
    )


def test_create_player_is_logged(client, make_exec, log_in):
    exec_user = make_exec()
    log_in()

    response = create_player(client)

    assert response.status_code == 201
    [entry] = audit_entries()
    assert entry.exec_id == exec_user.exec_id
    assert entry.action == "CREATE"
    assert entry.record_id == response.json()["player_id"]
    assert entry.new_values["kica_id"] == "K001"


def test_duplicate_kica_id_is_rejected_and_not_logged(client, make_exec, log_in):
    make_exec()
    log_in()
    create_player(client)

    response = create_player(client, name="Someone Else")

    assert response.status_code == 409
    assert len(audit_entries()) == 1


def test_update_logs_only_changed_fields(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    client.patch(f"/players/{player_id}", json={"name": "New Name", "kica_id": "K001"})

    entry = audit_entries()[-1]
    assert entry.action == "UPDATE"
    assert entry.old_values == {"name": "Player One"}
    assert entry.new_values == {"name": "New Name"}


def test_update_without_changes_is_not_logged(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    client.patch(f"/players/{player_id}", json={"name": "Player One"})

    assert len(audit_entries()) == 1


def test_status_change_is_logged(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    client.patch(f"/players/{player_id}/status", params={"is_active": False})

    entry = audit_entries()[-1]
    assert entry.old_values == {"is_active": True}
    assert entry.new_values == {"is_active": False}



def test_get_single_player(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    response = client.get(f"/players/{player_id}")

    assert response.status_code == 200
    assert response.json()["kica_id"] == "K001"
    assert client.get("/players/999").status_code == 404