def attend(client, session_date, player_ids):
    session_id = client.post("/sessions/", json={"session_date": session_date}).json()["session_id"]
    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": player_ids})


def pay(client, player_id, amount, paid_on="2026-10-20"):
    return client.post(
        "/payments/",
        json={"player_id": player_id, "amount": amount, "paid_on": paid_on, "method": "cash"}
    )


def spend(client, amount, expense_date="2026-10-20"):
    return client.post(
        "/expenses/",
        json={"description": "Hall rental", "amount": amount, "expense_date": expense_date}
    )


def receive(client, from_exec_id, amount):
    return client.post(
        "/transfers/",
        json={"from_exec_id": from_exec_id, "amount": amount, "transferred_on": "2026-10-20"}
    )


def switch_to(client, log_in, email):
    client.post("/auth/logout")
    log_in(email=email)


# --- Cash held and club balance ---

def test_dashboard_requires_login(client):
    assert client.get("/dashboard/").status_code == 401


def test_cash_held_follows_the_money(client, make_exec, log_in, make_player):
    srini = make_exec(email="srini@example.com", name="Srini")
    siva = make_exec(email="siva@example.com", name="Siva")
    alice = make_player()

    log_in(email="srini@example.com")
    pay(client, alice.player_id, "50.000")
    spend(client, "25.000")

    switch_to(client, log_in, "siva@example.com")
    pay(client, alice.player_id, "30.000")
    receive(client, srini.exec_id, "10.000")

    dashboard = client.get("/dashboard/").json()

    assert dashboard["cash_held"] == [
        {"exec_id": siva.exec_id, "name": "Siva", "amount": "40.000"},
        {"exec_id": srini.exec_id, "name": "Srini", "amount": "15.000"},
    ]
    assert dashboard["club_balance"] == "55.000"


def test_transfer_moves_cash_but_not_club_balance(client, make_exec, log_in, make_player):
    srini = make_exec(email="srini@example.com", name="Srini")
    siva = make_exec(email="siva@example.com", name="Siva")
    alice = make_player()

    log_in(email="srini@example.com")
    pay(client, alice.player_id, "20.000")

    switch_to(client, log_in, "siva@example.com")
    receive(client, srini.exec_id, "20.000")

    dashboard = client.get("/dashboard/").json()

    assert dashboard["cash_held"] == [
        {"exec_id": siva.exec_id, "name": "Siva", "amount": "20.000"}
    ]
    assert dashboard["club_balance"] == "20.000"


def test_reversed_records_are_ignored(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player()
    payment_id = pay(client, alice.player_id, "20.000").json()["payment_id"]

    client.post(f"/payments/{payment_id}/reverse", json={"reason": "Mistake"})
    dashboard = client.get("/dashboard/").json()

    assert dashboard["cash_held"] == []
    assert dashboard["club_balance"] == "0.000"


# --- Who owes ---

def test_outstanding_list_shows_only_owing_players_biggest_first(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    bob = make_player(name="Bob", kica_id="K002")
    chen = make_player(name="Chen", kica_id="K003")
    attend(client, "2026-09-25", [bob.player_id])
    attend(client, "2026-10-16", [alice.player_id, bob.player_id, chen.player_id])
    pay(client, bob.player_id, "3.000")
    pay(client, chen.player_id, "5.000")

    owing = client.get("/dashboard/outstanding").json()

    assert owing == [
        {"player_id": bob.player_id, "player_name": "Bob", "outstanding": "7.000"},
        {"player_id": alice.player_id, "player_name": "Alice", "outstanding": "5.000"},
    ]


def test_dashboard_totals_for_owing_and_credit(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    dan = make_player(name="Dan", kica_id="K004")
    attend(client, "2026-10-16", [alice.player_id, dan.player_id])
    pay(client, dan.player_id, "15.000")

    dashboard = client.get("/dashboard/").json()

    assert dashboard["total_outstanding"] == "5.000"
    assert dashboard["players_owing"] == 1
    assert dashboard["total_credit"] == "10.000"


def test_unpaid_for_a_month_uses_oldest_first(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    bob = make_player(name="Bob", kica_id="K002")
    attend(client, "2026-09-25", [bob.player_id])
    attend(client, "2026-10-16", [bob.player_id])
    pay(client, bob.player_id, "5.000")

    september = client.get("/dashboard/unpaid", params={"month": "2026-09-01"}).json()
    october = client.get("/dashboard/unpaid", params={"month": "2026-10-01"}).json()

    assert september == []
    assert october == [
        {"player_id": bob.player_id, "player_name": "Bob", "outstanding": "5.000"}
    ]


def test_unpaid_requires_a_month(client, make_exec, log_in):
    make_exec()
    log_in()

    assert client.get("/dashboard/unpaid").status_code == 422


# --- Month summary ---

def test_month_summary_counts_only_that_month(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    alice = make_player(name="Alice", kica_id="K001")
    bob = make_player(name="Bob", kica_id="K002")
    attend(client, "2026-09-25", [alice.player_id])
    attend(client, "2026-10-16", [alice.player_id, bob.player_id])
    attend(client, "2026-10-17", [alice.player_id])
    pay(client, bob.player_id, "5.000", paid_on="2026-09-30")
    pay(client, alice.player_id, "5.000", paid_on="2026-10-20")
    spend(client, "25.000", expense_date="2026-10-20")

    month = client.get("/dashboard/", params={"month": "2026-10-05"}).json()["month"]

    assert month == {
        "month": "2026-10-01",
        "sessions_held": 2,
        "players_attended": 2,
        "fees_assessed": "10.000",
        "payments_received": "5.000",
        "expenses_paid": "25.000"
    }


def test_active_players_excludes_inactive(client, make_exec, log_in, make_player):
    make_exec()
    log_in()
    make_player(name="Alice", kica_id="K001")
    make_player(name="Bob", kica_id="K002")
    make_player(name="Former", kica_id="K003", is_active=False)

    assert client.get("/dashboard/").json()["active_players"] == 2