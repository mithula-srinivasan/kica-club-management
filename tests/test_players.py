from datetime import timedelta

from sqlalchemy import select

from club_time import kuwait_today
from database import SessionLocal
from models import AuditLog


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


def player_details(**changes):
    """Everything a new player needs. Pass keyword arguments to change or add fields."""
    details = {
        "name": "Player One",
        "joined_on": "2026-01-10",
        "phone_1": "+965 5000 0000",
        "email": "parent@example.com",
        "date_of_birth": "2014-05-20",
        "parent_name": "Lakshmi",
    }
    details.update(changes)
    return details


def create_player(client, **changes):
    return client.post("/players/", json=player_details(**changes))


def test_create_player_is_logged(client, make_exec, log_in):
    exec_user = make_exec()
    log_in()

    response = create_player(client)

    assert response.status_code == 201
    [entry] = audit_entries()
    assert entry.exec_id == exec_user.exec_id
    assert entry.action == "CREATE"
    assert entry.record_id == response.json()["player_id"]
    assert entry.new_values["kica_id"] == "KICA001"
    assert entry.new_values["parent_name"] == "Lakshmi"


def test_new_players_get_kica_ids_in_order(client, make_exec, log_in):
    make_exec()
    log_in()

    first = create_player(client).json()
    second = create_player(client, name="Player Two").json()

    assert first["kica_id"] == "KICA001"
    assert second["kica_id"] == "KICA002"


def test_kica_id_continues_after_the_highest_number(client, make_exec, make_player, log_in):
    make_exec()
    log_in()
    make_player(name="Yokshith", kica_id="KICA057")
    make_player(name="Odd One", kica_id="K999")   # not KICA + digits, so ignored

    response = create_player(client)

    assert response.json()["kica_id"] == "KICA058"


def test_kica_id_cannot_be_chosen_or_changed(client, make_exec, log_in):
    make_exec()
    log_in()

    response = create_player(client, kica_id="KICA500")
    assert response.json()["kica_id"] == "KICA001"

    player_id = response.json()["player_id"]
    response = client.patch(f"/players/{player_id}", json={"kica_id": "KICA500"})

    assert response.status_code == 200
    assert response.json()["kica_id"] == "KICA001"
    assert len(audit_entries()) == 1


def test_update_logs_only_changed_fields(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    client.patch(f"/players/{player_id}", json={"name": "New Name", "parent_name": "Lakshmi"})

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
    assert response.json()["kica_id"] == "KICA001"
    assert client.get("/players/999").status_code == 404


def test_new_player_needs_every_required_field(client, make_exec, log_in):
    make_exec()
    log_in()

    for field in ["name", "phone_1", "email", "date_of_birth", "parent_name"]:
        details = player_details()
        del details[field]

        response = client.post("/players/", json=details)

        assert response.status_code == 422, field

    assert audit_entries() == []


def test_required_fields_cannot_be_just_spaces(client, make_exec, log_in):
    make_exec()
    log_in()

    response = create_player(client, parent_name="   ")

    assert response.status_code == 422
    assert response.json()["detail"] == "Parent name is required"


def test_stores_all_details_and_trims_spaces(client, make_exec, log_in):
    make_exec()
    log_in()

    response = create_player(
        client,
        name="  Arjun Kumar  ",
        parent_name="  Lakshmi Kumar ",
        phone_2="+965 6000 0000",
        fide_id="12345678",
        gender="male",
    )

    assert response.status_code == 201
    player = response.json()
    assert player["name"] == "Arjun Kumar"
    assert player["parent_name"] == "Lakshmi Kumar"
    assert player["phone_1"] == "+965 5000 0000"
    assert player["phone_2"] == "+965 6000 0000"
    assert player["email"] == "parent@example.com"
    assert player["fide_id"] == "12345678"
    assert player["gender"] == "male"
    assert player["date_of_birth"] == "2014-05-20"


def test_optional_details_can_be_cleared(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(
        client, phone_2="+965 6000 0000", fide_id="12345678", gender="female"
    ).json()["player_id"]

    response = client.patch(
        f"/players/{player_id}",
        json={"phone_2": "", "fide_id": "  ", "gender": None},
    )

    assert response.status_code == 200
    player = response.json()
    assert player["phone_2"] is None
    assert player["fide_id"] is None
    assert player["gender"] is None


def test_required_details_cannot_be_cleared(client, make_exec, log_in):
    make_exec()
    log_in()
    player_id = create_player(client).json()["player_id"]

    for field in ["name", "phone_1", "parent_name", "email", "date_of_birth"]:
        response = client.patch(f"/players/{player_id}", json={field: None})
        assert response.status_code == 422, field

    response = client.patch(f"/players/{player_id}", json={"parent_name": "   "})
    assert response.status_code == 422

    assert len(audit_entries()) == 1


def test_exec_can_replace_demo_details(client, make_exec, make_player, log_in):
    make_exec()
    log_in()
    player = make_player()

    response = client.patch(
        f"/players/{player.player_id}",
        json={"phone_1": "+965 5111 1111", "parent_name": "Ravi"},
    )

    assert response.status_code == 200
    assert response.json()["parent_name"] == "Ravi"
    entry = audit_entries()[-1]
    assert entry.old_values == {"phone_1": "+965 5000 0000", "parent_name": "Lakshmi"}
    assert entry.new_values == {"phone_1": "+965 5111 1111", "parent_name": "Ravi"}


def test_invalid_gender_and_email_are_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert create_player(client, gender="boy").status_code == 422
    assert create_player(client, email="not-an-email").status_code == 422


def test_date_of_birth_cannot_be_in_the_future(client, make_exec, log_in):
    make_exec()
    log_in()
    tomorrow = (kuwait_today() + timedelta(days=1)).isoformat()

    assert create_player(client, date_of_birth=tomorrow).status_code == 422

    player_id = create_player(client).json()["player_id"]
    response = client.patch(f"/players/{player_id}", json={"date_of_birth": tomorrow})
    assert response.status_code == 422


def test_next_kica_id_preview(client, make_exec, make_player, log_in):
    make_exec()
    log_in()

    assert client.get("/players/next-kica-id").json() == {"kica_id": "KICA001"}

    make_player(kica_id="KICA057")

    assert client.get("/players/next-kica-id").json() == {"kica_id": "KICA058"}