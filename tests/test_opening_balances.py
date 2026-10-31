from sqlalchemy import select

from database import SessionLocal
from models import AuditLog


def set_exec_opening(client, exec_id, amount, as_of="2026-09-30"):
    return client.put(
        f"/opening-balances/execs/{exec_id}",
        json={"amount": amount, "as_of": as_of}
    )


def set_player_opening(client, player_id, amount, as_of="2026-09-30"):
    return client.put(
        f"/opening-balances/players/{player_id}",
        json={"amount": amount, "as_of": as_of}
    )


def attend(client, session_date, player_ids):
    session_id = client.post("/sessions/", json={"session_date": session_date}).json()["session_id"]
    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": player_ids})


def pay(client, player_id, amount):
    return client.post(
        "/payments/",
        json={"player_id": player_id, "amount": amount, "paid_on": "2026-10-20", "method": "cash"}
    )


def statement(client, player_id):
    return client.get(f"/payments/players/{player_id}/statement").json()


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


# --- Permissions and validation ---

def test_regular_exec_cannot_set_opening_balances(client, make_exec, log_in):
    me = make_exec()
    log_in()

    assert set_exec_opening(client, me.exec_id, "100.000").status_code == 403


def test_exec_opening_cash_cannot_be_negative(client, make_exec, log_in):
    admin = make_exec(role="admin")
    log_in()

    assert set_exec_opening(client, admin.exec_id, "-5.000").status_code == 422


def test_as_of_date_cannot_be_in_the_future(client, make_exec, log_in):
    admin = make_exec(role="admin")
    log_in()

    assert set_exec_opening(client, admin.exec_id, "100.000", as_of="2099-01-01").status_code == 422


def test_pending_exec_cannot_have_opening_cash(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    pending = make_exec(email="pending@example.com", approved=False)
    log_in(email="admin@example.com")

    assert set_exec_opening(client, pending.exec_id, "50.000").status_code == 404


# --- Exec opening cash ---

def test_exec_opening_cash_is_added_to_cash_held(client, make_exec, log_in, make_player):
    admin = make_exec(role="admin", name="Mithula")
    log_in()
    alice = make_player()

    set_exec_opening(client, admin.exec_id, "120.000")
    pay(client, alice.player_id, "30.000")
    dashboard = client.get("/dashboard/").json()

    assert dashboard["cash_held"] == [
        {"exec_id": admin.exec_id, "name": "Mithula", "amount": "150.000"}
    ]
    assert dashboard["club_balance"] == "150.000"


def test_setting_again_replaces_and_is_logged(client, make_exec, log_in):
    admin = make_exec(role="admin")
    log_in()

    set_exec_opening(client, admin.exec_id, "100.000")
    set_exec_opening(client, admin.exec_id, "120.000")

    assert client.get("/dashboard/").json()["club_balance"] == "120.000"
    entry = audit_entries()[-1]
    assert entry.action == "UPDATE"
    assert entry.old_values == {"amount": "100.000", "as_of": "2026-09-30"}
    assert entry.new_values == {"amount": "120.000", "as_of": "2026-09-30"}


# --- Player opening balances ---

def test_opening_debt_is_paid_off_first(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    ahmed = make_player(name="Ahmed")
    set_player_opening(client, ahmed.player_id, "10.000")
    attend(client, "2026-10-16", [ahmed.player_id])

    pay(client, ahmed.player_id, "5.000")
    result = statement(client, ahmed.player_id)
    opening, october = result["months"]

    assert opening["is_opening_balance"] is True
    assert opening["amount_paid"] == "5.000"
    assert opening["remaining"] == "5.000"
    assert october["is_opening_balance"] is False
    assert october["remaining"] == "5.000"
    assert result["outstanding"] == "10.000"


def test_opening_credit_covers_future_fees(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    sara = make_player(name="Sara")
    set_player_opening(client, sara.player_id, "-15.000")
    attend(client, "2026-09-25", [sara.player_id])
    attend(client, "2026-10-16", [sara.player_id])

    result = statement(client, sara.player_id)

    assert result["outstanding"] == "0.000"
    assert result["credit"] == "5.000"


def test_player_with_only_opening_debt_appears_as_owing(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    ahmed = make_player(name="Ahmed")

    set_player_opening(client, ahmed.player_id, "10.000")
    owing = client.get("/dashboard/outstanding").json()

    assert owing == [
        {"player_id": ahmed.player_id, "player_name": "Ahmed", "outstanding": "10.000"}
    ]


def test_opening_credit_does_not_change_club_balance(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    sara = make_player(name="Sara")

    set_player_opening(client, sara.player_id, "-15.000")

    assert client.get("/dashboard/").json()["club_balance"] == "0.000"


def test_opening_balance_is_never_listed_as_a_months_unpaid_fee(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    ahmed = make_player(name="Ahmed")
    set_player_opening(client, ahmed.player_id, "10.000", as_of="2026-09-01")
    attend(client, "2026-10-16", [ahmed.player_id])

    september = client.get("/dashboard/unpaid", params={"month": "2026-09-01"}).json()
    october = client.get("/dashboard/unpaid", params={"month": "2026-10-01"}).json()

    assert september == []
    assert october == [
        {"player_id": ahmed.player_id, "player_name": "Ahmed", "outstanding": "5.000"}
    ]


# --- Listing and removing ---

def test_list_shows_both_kinds_with_names(client, make_exec, log_in, make_player):
    admin = make_exec(role="admin", name="Mithula")
    log_in()
    ahmed = make_player(name="Ahmed")
    set_exec_opening(client, admin.exec_id, "120.000")
    set_player_opening(client, ahmed.player_id, "10.000")

    result = client.get("/opening-balances/").json()

    assert result["execs"][0]["name"] == "Mithula"
    assert result["execs"][0]["set_by_name"] == "Mithula"
    assert result["players"][0]["player_name"] == "Ahmed"
    assert result["players"][0]["amount"] == "10.000"


def test_removing_an_opening_balance_undoes_its_effect(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    ahmed = make_player(name="Ahmed")
    set_player_opening(client, ahmed.player_id, "10.000")

    response = client.delete(f"/opening-balances/players/{ahmed.player_id}")

    assert response.status_code == 204
    assert client.get("/dashboard/outstanding").json() == []
    assert audit_entries()[-1].action == "DELETE"