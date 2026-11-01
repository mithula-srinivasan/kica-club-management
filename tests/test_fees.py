from datetime import date
from decimal import Decimal

from database import SessionLocal
from models import FeeRate


def attend(client, session_date, player_ids):
    session_id = client.post("/sessions/", json={"session_date": session_date}).json()["session_id"]
    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": player_ids})
    return session_id


def player_fees(client, player_id):
    return client.get(f"/fees/players/{player_id}").json()


def adjust(client, player_id, fee_month, amount_change, reason="Test reason"):
    return client.post(
        "/fees/adjustments",
        json={
            "player_id": player_id,
            "fee_month": fee_month,
            "amount_change": amount_change,
            "reason": reason
        }
    )


def test_one_session_means_one_fee(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])

    [fee] = player_fees(client, alice.player_id)

    assert fee["fee_month"] == "2026-10-01"
    assert fee["amount_due"] == "5.000"


def test_many_sessions_in_a_month_still_one_fee(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])
    attend(client, "2026-10-17", [alice.player_id])
    attend(client, "2026-10-23", [alice.player_id])

    fees = player_fees(client, alice.player_id)

    assert len(fees) == 1
    assert fees[0]["amount_due"] == "5.000"


def test_each_month_attended_is_charged(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-09-25", [alice.player_id])
    attend(client, "2026-10-16", [alice.player_id])

    fees = player_fees(client, alice.player_id)

    assert [fee["fee_month"] for fee in fees] == ["2026-09-01", "2026-10-01"]


def test_no_attendance_means_no_fee(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    bob = make_player(name="Bob", kica_id="K002")
    attend(client, "2026-10-16", [alice.player_id])

    assert player_fees(client, bob.player_id) == []


def test_attendance_correction_removes_fee(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    session_id = attend(client, "2026-10-16", [alice.player_id])

    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": []})

    assert player_fees(client, alice.player_id) == []


def test_admin_can_waive_a_fee(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])

    response = adjust(client, alice.player_id, "2026-10-01", "-5.000", reason="Scholarship")

    assert response.status_code == 201
    assert response.json()["adjustments"] == "-5.000"
    assert response.json()["amount_due"] == "0.000"


def test_regular_exec_cannot_adjust_fees(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()

    assert adjust(client, alice.player_id, "2026-10-01", "-5.000").status_code == 403


def test_adjustment_cannot_make_fee_negative(client, make_exec, log_in, make_player):
    make_exec(role="admin")
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])
    adjust(client, alice.player_id, "2026-10-01", "-5.000")

    assert adjust(client, alice.player_id, "2026-10-01", "-1.000").status_code == 409


def test_month_view_lists_players_by_name(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    bob = make_player(name="Bob", kica_id="K002")
    alice = make_player(name="Alice", kica_id="K001")
    attend(client, "2026-10-16", [bob.player_id, alice.player_id])

    fees = client.get("/fees/month", params={"month": "2026-10-16"}).json()

    assert [fee["player_name"] for fee in fees] == ["Alice", "Bob"]


def test_new_rate_applies_only_from_its_start(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    with SessionLocal() as db:
        db.add(FeeRate(monthly_amount=Decimal("6.000"), effective_from=date(2027, 1, 1)))
        db.commit()
    attend(client, "2026-12-18", [alice.player_id])
    attend(client, "2027-01-15", [alice.player_id])

    fees = player_fees(client, alice.player_id)

    assert [fee["amount_due"] for fee in fees] == ["5.000", "6.000"]



def add_rate(client, amount, effective_from):
    return client.post(
        "/fees/rates",
        json={"monthly_amount": amount, "effective_from": effective_from}
    )


def test_admin_can_set_a_future_rate(client, make_exec, log_in, make_player):
    make_exec(role="admin", name="Mithula")
    log_in()
    alice = make_player()

    response = add_rate(client, "6.000", "2030-01-15")
    attend(client, "2030-01-10", [alice.player_id])

    assert response.status_code == 201
    assert response.json()["effective_from"] == "2030-01-01"
    assert response.json()["changed_by_name"] == "Mithula"
    assert player_fees(client, alice.player_id)[0]["amount_due"] == "6.000"


def test_new_rate_cannot_start_in_a_past_month(client, make_exec, log_in):
    make_exec(role="admin")
    log_in()

    assert add_rate(client, "6.000", "2020-01-01").status_code == 422


def test_only_one_rate_can_start_in_a_month(client, make_exec, log_in):
    make_exec(role="admin")
    log_in()
    add_rate(client, "6.000", "2030-01-01")

    assert add_rate(client, "7.000", "2030-01-01").status_code == 409


def test_regular_exec_cannot_change_the_rate(client, make_exec, log_in):
    make_exec()
    log_in()

    assert add_rate(client, "6.000", "2030-01-01").status_code == 403


def test_upcoming_rate_can_be_removed_but_started_rate_cannot(client, make_exec, log_in):
    make_exec(role="admin")
    log_in()
    upcoming_id = add_rate(client, "6.000", "2030-01-01").json()["fee_rate_id"]
    rates = client.get("/fees/rates").json()
    started_id = next(r["fee_rate_id"] for r in rates if r["effective_from"] == "2000-01-01")

    assert client.delete(f"/fees/rates/{upcoming_id}").status_code == 204
    assert client.delete(f"/fees/rates/{started_id}").status_code == 409