def create_player(client, kica_id="K001", name=None):
    # Each player needs a different name now (name + date of birth must be unique)
    return client.post(
        "/players/",
        json={
            "name": name or f"Player {kica_id}",
            "joined_on": "2026-01-10",
            "phone_1": "+965 5000 0000",
            "email": "parent@example.com",
            "date_of_birth": "2014-05-20",
            "parent_name": "Lakshmi",
            "country": "India",
            "gender": "male",
        }
    ).json()["player_id"]

def test_regular_exec_cannot_view_audit_log(client, make_exec, log_in):
    make_exec()
    log_in()

    assert client.get("/audit-logs/").status_code == 403


def test_admin_sees_entries_newest_first_with_names(client, make_exec, log_in):
    make_exec(role="admin", name="Mithula")
    log_in()
    first_id = create_player(client, kica_id="K001")
    second_id = create_player(client, kica_id="K002")

    entries = client.get("/audit-logs/").json()

    assert [e["record_id"] for e in entries] == [second_id, first_id]
    assert entries[0]["exec_name"] == "Mithula"
    assert entries[0]["action"] == "CREATE"
    assert entries[0]["old_values"] is None


def test_filter_by_table_and_record(client, make_exec, log_in):
    make_exec(role="admin")
    log_in()
    player_id = create_player(client)
    client.patch(f"/players/{player_id}", json={"name": "New Name"})
    client.post("/sessions/", json={"session_date": "2026-10-16"})

    entries = client.get(
        "/audit-logs/",
        params={"table_name": "players", "record_id": player_id}
    ).json()

    assert [e["action"] for e in entries] == ["UPDATE", "CREATE"]


def test_filter_by_exec(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    other = make_exec(email="other@example.com")

    log_in(email="other@example.com")
    create_player(client, kica_id="K001")
    client.post("/auth/logout")

    log_in(email="admin@example.com")
    create_player(client, kica_id="K002")

    entries = client.get("/audit-logs/", params={"exec_id": other.exec_id}).json()

    assert len(entries) == 1
    assert entries[0]["exec_id"] == other.exec_id


def test_limit_returns_only_newest(client, make_exec, log_in):
    make_exec(role="admin")
    log_in()
    create_player(client, kica_id="K001")
    create_player(client, kica_id="K002")
    newest_id = create_player(client, kica_id="K003")

    entries = client.get("/audit-logs/", params={"limit": 1}).json()

    assert [e["record_id"] for e in entries] == [newest_id]
    assert client.get("/audit-logs/", params={"limit": 0}).status_code == 422