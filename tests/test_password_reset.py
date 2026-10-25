import pytest


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []

    def fake_send_email(to, subject, text):
        emails.append({"to": to, "subject": subject, "text": text})

    # Capture emails instead of sending them
    monkeypatch.setattr("routers.auth.send_email", fake_send_email)

    return emails


def token_from(email):
    return email["text"].split("#token=")[1].split()[0]


def request_reset(client, email="exec@example.com"):
    return client.post("/auth/forgot-password", json={"email": email})


def reset(client, token, new_password="brand-new-password"):
    return client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": new_password}
    )


def test_forgot_password_sends_link(client, make_exec, sent_emails):
    make_exec()

    response = request_reset(client)

    assert response.status_code == 200
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "exec@example.com"


def test_unknown_email_gets_same_reply_and_no_email(client, make_exec, sent_emails):
    make_exec()

    real = request_reset(client)
    sent_emails.clear()
    unknown = request_reset(client, email="nobody@example.com")

    assert unknown.status_code == 200
    assert unknown.json() == real.json()
    assert sent_emails == []


def test_reset_changes_password(client, make_exec, log_in, sent_emails):
    make_exec()
    request_reset(client)

    assert reset(client, token_from(sent_emails[0])).status_code == 200
    assert log_in(password="correct-password").status_code == 401
    assert log_in(password="brand-new-password").status_code == 200


def test_reset_link_works_only_once(client, make_exec, sent_emails):
    make_exec()
    request_reset(client)
    token = token_from(sent_emails[0])

    assert reset(client, token).status_code == 200
    assert reset(client, token, new_password="another-new-password").status_code == 400


def test_only_newest_link_works(client, make_exec, sent_emails):
    make_exec()
    request_reset(client)
    request_reset(client)
    old_token = token_from(sent_emails[0])
    new_token = token_from(sent_emails[1])

    assert reset(client, old_token).status_code == 400
    assert reset(client, new_token).status_code == 200


def test_reset_logs_out_everywhere(client, make_exec, log_in, sent_emails):
    make_exec()
    log_in()
    request_reset(client)

    reset(client, token_from(sent_emails[0]))

    assert client.get("/players/").status_code == 401