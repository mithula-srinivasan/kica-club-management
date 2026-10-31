from sqlalchemy import select

from database import SessionLocal
from models import AuditLog, Expense


def spend(client, amount="25.000", **extra):
    data = {"description": "Hall rental - October", "amount": amount, "expense_date": "2026-10-20"}
    data.update(extra)
    return client.post("/expenses/", json=data)


def audit_entries():
    with SessionLocal() as db:
        return db.scalars(select(AuditLog).order_by(AuditLog.audit_id)).all()


# --- Recording expenses ---

def test_expenses_require_login(client):
    assert client.get("/expenses/").status_code == 401


def test_expense_is_paid_and_recorded_by_logged_in_exec(client, make_exec, log_in):
    me = make_exec(name="Siva")
    log_in()

    response = spend(client)

    assert response.status_code == 201
    assert response.json()["recorded_by_name"] == "Siva"
    assert response.json()["amount"] == "25.000"

    with SessionLocal() as db:
        expense = db.get(Expense, response.json()["expense_id"])

    assert expense.paid_by_exec_id == me.exec_id
    assert expense.recorded_by_exec_id == me.exec_id
    assert expense.funding_source == "club_funds"


def test_new_expense_is_logged(client, make_exec, log_in):
    make_exec()
    log_in()

    expense_id = spend(client).json()["expense_id"]

    [entry] = audit_entries()
    assert entry.action == "CREATE"
    assert entry.table_name == "expenses"
    assert entry.record_id == expense_id


def test_expenses_are_listed_newest_first(client, make_exec, log_in):
    make_exec()
    log_in()
    spend(client, description="September hall", expense_date="2026-09-18")
    spend(client, description="October hall", expense_date="2026-10-16")

    expenses = client.get("/expenses/").json()

    assert [e["description"] for e in expenses] == ["October hall", "September hall"]


def test_future_expense_date_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert spend(client, expense_date="2099-01-01").status_code == 422


def test_blank_description_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert spend(client, description="   ").status_code == 422


def test_zero_amount_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert spend(client, amount="0").status_code == 422


# --- Reversals ---

def test_reversal_marks_expense_and_logs_reason(client, make_exec, log_in):
    make_exec()
    log_in()
    expense_id = spend(client).json()["expense_id"]

    response = client.post(f"/expenses/{expense_id}/reverse", json={"reason": "Wrong amount"})

    assert response.json()["status"] == "reversed"
    entry = audit_entries()[-1]
    assert entry.action == "REVERSE"
    assert entry.new_values == {"status": "reversed", "reason": "Wrong amount"}


def test_exec_cannot_reverse_someone_elses_expense(client, make_exec, log_in):
    make_exec(email="a@example.com")
    make_exec(email="b@example.com")
    log_in(email="a@example.com")
    expense_id = spend(client).json()["expense_id"]
    client.post("/auth/logout")
    log_in(email="b@example.com")

    response = client.post(f"/expenses/{expense_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 403


def test_admin_can_reverse_any_expense(client, make_exec, log_in):
    make_exec(email="a@example.com")
    make_exec(email="admin@example.com", role="admin")
    log_in(email="a@example.com")
    expense_id = spend(client).json()["expense_id"]
    client.post("/auth/logout")
    log_in(email="admin@example.com")

    response = client.post(f"/expenses/{expense_id}/reverse", json={"reason": "Mistake"})

    assert response.status_code == 200


def test_expense_cannot_be_reversed_twice(client, make_exec, log_in):
    make_exec()
    log_in()
    expense_id = spend(client).json()["expense_id"]
    client.post(f"/expenses/{expense_id}/reverse", json={"reason": "Mistake"})

    response = client.post(f"/expenses/{expense_id}/reverse", json={"reason": "Again"})

    assert response.status_code == 409