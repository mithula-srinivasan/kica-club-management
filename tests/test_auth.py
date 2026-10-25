def log_in(client, email="exec@example.com", password="correct-password", remember_me=False):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password, "remember_me": remember_me}
    )


def test_login_with_correct_password(client, make_exec):
    make_exec()

    response = log_in(client)

    assert response.status_code == 200
    assert "kica_session" in response.cookies


def test_login_with_wrong_password(client, make_exec):
    make_exec()

    response = log_in(client, password="wrong-password")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_with_unknown_email(client):
    response = log_in(client, email="nobody@example.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_pending_account_cannot_log_in(client, make_exec):
    make_exec(approved=False)

    response = log_in(client)

    assert response.status_code == 403


def test_deactivated_account_cannot_log_in(client, make_exec):
    make_exec(is_active=False)

    response = log_in(client)

    assert response.status_code == 401


def test_players_require_login(client):
    response = client.get("/players/")

    assert response.status_code == 401


def test_players_work_after_login(client, make_exec):
    make_exec()
    log_in(client)

    response = client.get("/players/")

    assert response.status_code == 200


def test_logout_ends_session(client, make_exec):
    make_exec()
    log_in(client)

    client.post("/auth/logout")
    response = client.get("/players/")

    assert response.status_code == 401


def test_me_never_shows_password_hash(client, make_exec):
    make_exec(name="Ahmed")
    log_in(client)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["name"] == "Ahmed"
    assert "password_hash" not in response.json()
    