from io import BytesIO

from openpyxl import load_workbook


def setup_club(client, make_player):
    alice = make_player(name="Alice")
    session_id = client.post("/sessions/", json={"session_date": "2026-10-16"}).json()["session_id"]
    client.put(f"/sessions/{session_id}/attendance", json={"player_ids": [alice.player_id]})
    client.post(
        "/payments/",
        json={"player_id": alice.player_id, "amount": "3.000", "paid_on": "2026-10-20", "method": "cash"}
    )


def test_regular_exec_cannot_export(client, make_exec, log_in):
    make_exec()
    log_in()

    assert client.get("/exports/club-data").status_code == 403


def test_admin_downloads_excel_workbook(client, make_exec, log_in, make_player):
    make_exec(role="admin", name="Mithula")
    log_in()
    setup_club(client, make_player)

    response = client.get("/exports/club-data")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert ".xlsx" in response.headers["content-disposition"]

    workbook = load_workbook(BytesIO(response.content))

    assert workbook.sheetnames == [
        "Summary", "Players", "Monthly fees", "Payments",
        "Expenses", "Income", "Transfers", "Attendance", "Opening balances"
    ]


def test_export_figures_match_the_app(client, make_exec, log_in, make_player):
    make_exec(role="admin", name="Mithula")
    log_in()
    setup_club(client, make_player)

    workbook = load_workbook(BytesIO(client.get("/exports/club-data").content))

    summary = {row[0]: row[1] for row in workbook["Summary"].iter_rows(values_only=True)}
    assert summary["Club balance (KWD)"] == 3
    assert summary["Owed by members (KWD)"] == 2

    [header, payment] = workbook["Payments"].iter_rows(values_only=True)
    assert payment[2] == "Alice"
    assert payment[3] == 3
    assert payment[6] == "Mithula"

    [header, fee] = workbook["Monthly fees"].iter_rows(values_only=True)
    assert fee[0] == "Alice"
    assert fee[3:] == (5, 3, 2)

    [header, attended] = workbook["Attendance"].iter_rows(values_only=True)
    assert attended[1] == "Alice"