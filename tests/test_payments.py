from sqlalchemy import select

from database import SessionLocal
from models import AuditLog, Payment


def attend(client, session_date, player_ids):
    session_id = client.post("/sessions/", json={"session_date": session_date}).json()["session_id"]
    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": player_ids})


def pay(client, player_id, amount, **extra):
    data = {"player_id": player_id, "amount": amount, "paid_on": "2026-10-20", "method": "cash"}
    data.update(extra)
    return client.post("/payments/", json=data)


def statement(client, player_id):
    return client.get(f"/payments/players/{player_id}/statement").json()


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


# --- Recording payments ---

def test_payment_is_collected_and_recorded_by_logged_in_exec(client, make_exec, log_in, make_player):
    me = make_exec(name="Mithula")
    log_in()
    alice = make_player()

    response = pay(client, alice.player_id, "5.000")

    assert response.status_code == 201
    assert response.json()["recorded_by_name"] == "Mithula"
    assert response.json()["amount"] == "5.000"

    with SessionLocal() as db:
        payment = db.get(Payment, response.json()["payment_id"])

    assert payment.collected_by_exec_id == me.exec_id
    assert payment.recorded_by_exec_id == me.exec_id


def test_same_form_submitted_twice_records_once(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()

    first = pay(client, alice.player_id, "5.000", idempotency_key="form-123")
    second = pay(client, alice.player_id, "5.000", idempotency_key="form-123")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["payment_id"] == first.json()["payment_id"]
    assert len(client.get("/payments/").json()) == 1


def test_future_payment_date_is_rejected(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()

    assert pay(client, alice.player_id, "5.000", paid_on="2099-01-01").status_code == 422


def test_zero_amount_is_rejected(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()

    assert pay(client, alice.player_id, "0").status_code == 422


def test_unknown_method_is_rejected(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()

    assert pay(client, alice.player_id, "5.000", method="cheque").status_code == 422


def test_unknown_player_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert pay(client, 999, "5.000").status_code == 404


# --- Balances ---

def test_partial_payment_leaves_outstanding(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])

    pay(client, alice.player_id, "3.000")
    result = statement(client, alice.player_id)

    assert result["outstanding"] == "2.000"
    assert result["months"][0]["amount_paid"] == "3.000"
    assert result["months"][0]["remaining"] == "2.000"


def test_payment_covers_oldest_month_first(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-09-25", [alice.player_id])
    attend(client, "2026-10-16", [alice.player_id])

    pay(client, alice.player_id, "7.000")
    september, october = statement(client, alice.player_id)["months"]

    assert september["remaining"] == "0.000"
    assert october["amount_paid"] == "2.000"
    assert october["remaining"] == "3.000"


def test_advance_payment_becomes_credit(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])

    pay(client, alice.player_id, "15.000")
    result = statement(client, alice.player_id)

    assert result["outstanding"] == "0.000"
    assert result["credit"] == "10.000"


def test_credit_covers_a_new_fee_automatically(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    pay(client, alice.player_id, "5.000")
    assert statement(client, alice.player_id)["credit"] == "5.000"

    attend(client, "2026-10-16", [alice.player_id])
    result = statement(client, alice.player_id)

    assert result["outstanding"] == "0.000"
    assert result["credit"] == "0.000"


# --- Reversals ---

def test_reversed_payment_no_longer_counts(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    attend(client, "2026-10-16", [alice.player_id])
    payment_id = pay(client, alice.player_id, "5.000").json()["payment_id"]

    response = client.post(f"/payments/{payment_id}/reverse", json={"reason": "Entered twice"})

    assert response.json()["status"] == "reversed"
    assert statement(client, alice.player_id)["outstanding"] == "5.000"


def test_reversal_is_logged_with_reason(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    payment_id = pay(client, alice.player_id, "5.000").json()["payment_id"]

    client.post(f"/payments/{payment_id}/reverse", json={"reason": "Entered twice"})

    entry = audit_entries()[-1]
    assert entry.action == "REVERSE"
    assert entry.record_id == payment_id
    assert entry.new_values == {"status": "reversed", "reason": "Entered twice"}


def test_exec_cannot_reverse_someone_elses_payment(client, make_exec, log_in, make_player):
    make_exec(email="a@example.com")
    make_exec(email="b@example.com")
    alice = make_player()
    log_in(email="a@example.com")
    payment_id = pay(client, alice.player_id, "5.000").json()["payment_id"]
    client.post("/auth/logout")
    log_in(email="b@example.com")

    response = client.post(f"/payments/{payment_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 403


def test_admin_can_reverse_any_payment(client, make_exec, log_in, make_player):
    make_exec(email="a@example.com")
    make_exec(email="admin@example.com", role="admin")
    alice = make_player()
    log_in(email="a@example.com")
    payment_id = pay(client, alice.player_id, "5.000").json()["payment_id"]
    client.post("/auth/logout")
    log_in(email="admin@example.com")

    response = client.post(f"/payments/{payment_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 200


def test_payment_cannot_be_reversed_twice(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    payment_id = pay(client, alice.player_id, "5.000").json()["payment_id"]
    client.post(f"/payments/{payment_id}/reverse", json={"reason": "Mistake"})

    response = client.post(f"/payments/{payment_id}/reverse", json={"reason": "Again"})

    assert response.status_code == 409


def test_admin_records_payment_collected_by_another_exec(client, make_exec, log_in, make_player):
    make_exec(email="admin@example.com", name="Siva", role="admin")
    srinadh = make_exec(email="srinadh@example.com", name="Srinadh")
    log_in(email="admin@example.com")
    alice = make_player()

    response = pay(client, alice.player_id, "5.000", collected_by_exec_id=srinadh.exec_id)

    assert response.status_code == 201
    assert response.json()["collected_by_name"] == "Srinadh"
    assert response.json()["recorded_by_name"] == "Siva"

    cash_held = client.get("/dashboard/").json()["cash_held"]
    assert cash_held == [{"exec_id": srinadh.exec_id, "name": "Srinadh", "amount": "5.000"}]


def test_regular_exec_cannot_record_on_behalf_of_another(client, make_exec, log_in, make_player):
    make_exec(email="a@example.com")
    other = make_exec(email="b@example.com")
    log_in(email="a@example.com")
    alice = make_player()

    response = pay(client, alice.player_id, "5.000", collected_by_exec_id=other.exec_id)

    assert response.status_code == 403