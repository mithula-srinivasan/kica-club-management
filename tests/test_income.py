def earn(client, amount="50.000", **extra):
    data = {"description": "Tournament entry fees", "amount": amount, "income_date": "2026-10-20"}
    data.update(extra)
    return client.post("/income/", json=data)


def test_income_requires_login(client):
    assert client.get("/income/").status_code == 401


def test_income_is_received_by_the_recorder_and_adds_to_club_balance(client, make_exec, log_in):
    me = make_exec(name="Siva")
    log_in()

    response = earn(client)

    assert response.status_code == 201
    assert response.json()["received_by_name"] == "Siva"
    assert response.json()["recorded_by_name"] == "Siva"

    dashboard = client.get("/dashboard/").json()
    assert dashboard["club_balance"] == "50.000"
    assert dashboard["cash_held"] == [{"exec_id": me.exec_id, "name": "Siva", "amount": "50.000"}]


def test_income_appears_in_the_month_summary(client, make_exec, log_in):
    make_exec()
    log_in()
    earn(client, income_date="2026-10-20")
    earn(client, amount="30.000", income_date="2026-09-15")

    month = client.get("/dashboard/", params={"month": "2026-10-01"}).json()["month"]

    assert month["income_received"] == "50.000"


def test_reversed_income_no_longer_counts(client, make_exec, log_in):
    make_exec()
    log_in()
    income_id = earn(client).json()["income_id"]

    response = client.post(f"/income/{income_id}/reverse", json={"reason": "Entered twice"})

    assert response.json()["status"] == "reversed"
    assert client.get("/dashboard/").json()["club_balance"] == "0.000"


def test_admin_records_income_received_by_another_exec(client, make_exec, log_in):
    make_exec(email="admin@example.com", name="Siva", role="admin")
    gowri = make_exec(email="gowri@example.com", name="Gowri")
    log_in(email="admin@example.com")

    response = earn(client, received_by_exec_id=gowri.exec_id)

    assert response.json()["received_by_name"] == "Gowri"
    assert response.json()["recorded_by_name"] == "Siva"


def test_regular_exec_cannot_record_income_for_another(client, make_exec, log_in):
    make_exec(email="a@example.com")
    other = make_exec(email="b@example.com")
    log_in(email="a@example.com")

    assert earn(client, received_by_exec_id=other.exec_id).status_code == 403


def test_future_income_date_is_rejected(client, make_exec, log_in):
    make_exec()
    log_in()

    assert earn(client, income_date="2099-01-01").status_code == 422


def test_income_cannot_be_reversed_twice(client, make_exec, log_in):
    make_exec()
    log_in()
    income_id = earn(client).json()["income_id"]
    client.post(f"/income/{income_id}/reverse", json={"reason": "Mistake"})

    response = client.post(f"/income/{income_id}/reverse", json={"reason": "Again"})

    assert response.status_code == 409