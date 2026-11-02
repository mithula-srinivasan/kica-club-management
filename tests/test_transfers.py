from sqlalchemy import select

from database import SessionLocal
from models import AuditLog


def receive(client, from_exec_id, amount="20.000", **extra):
    data = {"from_exec_id": from_exec_id, "amount": amount, "transferred_on": "2026-10-20"}
    data.update(extra)
    return client.post("/transfers/", json=data)


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


# --- Recording transfers ---

def test_transfers_require_login(client):
    assert client.get("/transfers/").status_code == 401


def test_receiver_records_the_transfer(client, make_exec, log_in):
    siva = make_exec(name="Siva")
    srini = make_exec(email="srini@example.com", name="Srini")
    log_in()

    response = receive(client, srini.exec_id)

    assert response.status_code == 201
    body = response.json()
    assert body["from_exec_name"] == "Srini"
    assert body["to_exec_id"] == siva.exec_id
    assert body["recorded_by_exec_id"] == siva.exec_id
    assert body["amount"] == "20.000"


def test_transfer_date_comes_back_unchanged(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()

    response = receive(client, srini.exec_id, transferred_on="2026-10-20")

    assert response.json()["transferred_on"] == "2026-10-20"


def test_identical_transfers_on_same_day_are_allowed(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()

    assert receive(client, srini.exec_id).status_code == 201
    assert receive(client, srini.exec_id).status_code == 201
    assert len(client.get("/transfers/").json()) == 2


def test_new_transfer_is_logged(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()

    transfer_id = receive(client, srini.exec_id).json()["transfer_id"]

    [entry] = audit_entries()
    assert entry.action == "CREATE"
    assert entry.table_name == "transfers"
    assert entry.record_id == transfer_id


def test_cannot_receive_from_yourself(client, make_exec, log_in):
    me = make_exec()
    log_in()

    assert receive(client, me.exec_id).status_code == 422


def test_giver_must_be_approved_but_may_be_inactive(client, make_exec, log_in):
    make_exec()
    former = make_exec(email="former@example.com", is_active=False)
    pending = make_exec(email="pending@example.com", approved=False)
    log_in()

    # Someone who has left may have handed over money before going
    assert receive(client, former.exec_id).status_code == 201

    # A sign-up that was never approved can't have handled club money
    assert receive(client, pending.exec_id).status_code == 422


def test_future_transfer_date_is_rejected(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()

    assert receive(client, srini.exec_id, transferred_on="2099-01-01").status_code == 422


def test_zero_amount_is_rejected(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()

    assert receive(client, srini.exec_id, amount="0").status_code == 422


def test_other_execs_list_excludes_self_and_inactive(client, make_exec, log_in):
    make_exec(name="Me")
    make_exec(email="srini@example.com", name="Srini")
    make_exec(email="former@example.com", name="Former", is_active=False)
    make_exec(email="pending@example.com", name="Pending", approved=False)
    log_in()

    names = [e["name"] for e in client.get("/transfers/other-execs").json()]

    assert names == ["Srini"]


# --- Reversals ---

def test_reversal_marks_transfer_and_logs_reason(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()
    transfer_id = receive(client, srini.exec_id).json()["transfer_id"]

    response = client.post(f"/transfers/{transfer_id}/reverse", json={"reason": "Wrong amount"})

    assert response.json()["status"] == "reversed"
    entry = audit_entries()[-1]
    assert entry.action == "REVERSE"
    assert entry.new_values == {"status": "reversed", "reason": "Wrong amount"}


def test_giver_cannot_reverse_a_transfer_they_did_not_record(client, make_exec, log_in):
    make_exec(email="siva@example.com")
    srini = make_exec(email="srini@example.com")
    log_in(email="siva@example.com")
    transfer_id = receive(client, srini.exec_id).json()["transfer_id"]
    client.post("/auth/logout")
    log_in(email="srini@example.com")

    response = client.post(f"/transfers/{transfer_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 403


def test_admin_can_reverse_any_transfer(client, make_exec, log_in):
    make_exec(email="siva@example.com")
    srini = make_exec(email="srini@example.com")
    make_exec(email="admin@example.com", role="admin")
    log_in(email="siva@example.com")
    transfer_id = receive(client, srini.exec_id).json()["transfer_id"]
    client.post("/auth/logout")
    log_in(email="admin@example.com")

    response = client.post(f"/transfers/{transfer_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 200


def test_transfer_cannot_be_reversed_twice(client, make_exec, log_in):
    make_exec()
    srini = make_exec(email="srini@example.com")
    log_in()
    transfer_id = receive(client, srini.exec_id).json()["transfer_id"]
    client.post(f"/transfers/{transfer_id}/reverse", json={"reason": "Mistake"})

    response = client.post(f"/transfers/{transfer_id}/reverse", json={"reason": "Again"})

    assert response.status_code == 409



def test_admin_records_transfer_between_two_other_execs(client, make_exec, log_in):
    make_exec(email="admin@example.com", name="Siva", role="admin")
    srini = make_exec(email="srini@example.com", name="Srini")
    vidya = make_exec(email="vidya@example.com", name="Vidya")
    log_in(email="admin@example.com")

    response = receive(client, srini.exec_id, to_exec_id=vidya.exec_id)

    assert response.status_code == 201
    assert response.json()["from_exec_name"] == "Srini"
    assert response.json()["to_exec_name"] == "Vidya"
    assert response.json()["recorded_by_name"] == "Siva"


def test_regular_exec_cannot_record_transfer_for_another_receiver(client, make_exec, log_in):
    make_exec(email="a@example.com")
    srini = make_exec(email="srini@example.com")
    vidya = make_exec(email="vidya@example.com")
    log_in(email="a@example.com")

    assert receive(client, srini.exec_id, to_exec_id=vidya.exec_id).status_code == 403


def test_giver_and_receiver_must_be_different(client, make_exec, log_in):
    make_exec(email="admin@example.com", role="admin")
    srini = make_exec(email="srini@example.com")
    log_in(email="admin@example.com")

    assert receive(client, srini.exec_id, to_exec_id=srini.exec_id).status_code == 422