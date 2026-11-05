from datetime import timedelta

import pytest
from sqlalchemy import select

from club_time import kuwait_today
from database import SessionLocal
from models import AuditLog, PlayerRegistration


@pytest.fixture
def sent_emails(monkeypatch):
    emails = []

    def fake_send_email(to, subject, text):
        emails.append({"to": to, "subject": subject, "text": text})

    # Capture emails instead of sending them
    monkeypatch.setattr("routers.registrations.send_email", fake_send_email)

    return emails


def registration_details(**changes):
    """A valid Join form. Pass keyword arguments to change or add fields."""
    details = {
        "name": "Arjun Kumar",
        "parent_name": "Lakshmi Kumar",
        "phone_1": "+965 5000 0000",
        "email": "parent@example.com",
        "date_of_birth": "2014-05-20",
        "consent": True,
    }
    details.update(changes)
    return details


def register(client, **changes):
    return client.post("/registrations/", json=registration_details(**changes))


def saved_registrations():
    with SessionLocal() as db:
        return db.scalars(
            select(PlayerRegistration).order_by(PlayerRegistration.registration_id)
        ).all()


def test_anyone_can_register_without_logging_in(client, sent_emails):
    response = register(client)

    assert response.status_code == 201
    [registration] = saved_registrations()
    assert registration.name == "Arjun Kumar"
    assert registration.status == "pending"
    assert registration.consented_at is not None
    assert registration.reviewed_at is None


def test_thank_you_email_is_sent_to_the_parent(client, sent_emails):
    register(client)

    [email] = sent_emails
    assert email["to"] == "parent@example.com"
    assert email["subject"] == "Thank you for registering with KICA"
    assert "Dear Lakshmi Kumar" in email["text"]
    assert "Arjun Kumar" in email["text"]
    assert "please contact us at" in email["text"]


def test_consent_box_must_be_ticked(client, sent_emails):
    response = register(client, consent=False)

    assert response.status_code == 422
    assert response.json()["detail"] == "Please tick the box to agree to the club rules"
    assert saved_registrations() == []
    assert sent_emails == []


def test_required_details_are_needed(client, sent_emails):
    details = registration_details()
    del details["parent_name"]

    assert client.post("/registrations/", json=details).status_code == 422
    assert register(client, name="   ").status_code == 422
    assert saved_registrations() == []


def test_birthday_cannot_be_in_the_future(client, sent_emails):
    tomorrow = (kuwait_today() + timedelta(days=1)).isoformat()

    assert register(client, date_of_birth=tomorrow).status_code == 422


def test_same_name_and_birthday_as_a_player_is_refused(client, make_player, sent_emails):
    make_player(name="Arjun Kumar")   # make_player's date of birth is 2014-05-20

    response = register(client, name="  arjun   KUMAR ")

    assert response.status_code == 409
    assert response.json()["detail"].startswith(
        "A player with this name and date of birth is already registered."
    )
    assert saved_registrations() == []
    assert sent_emails == []


def test_same_name_and_birthday_as_a_waiting_registration_is_refused(client, sent_emails):
    register(client)

    response = register(client, parent_name="Someone Else")

    assert response.status_code == 409
    assert len(saved_registrations()) == 1


def test_same_name_with_a_different_birthday_is_allowed(client, make_player, sent_emails):
    make_player(name="Arjun Kumar")

    assert register(client, date_of_birth="2015-01-01").status_code == 201


def test_spam_bots_are_ignored(client, sent_emails):
    response = register(client, website="http://spam.example.com")

    # Looks like it worked, but nothing is saved or sent
    assert response.status_code == 201
    assert saved_registrations() == []
    assert sent_emails == []


def test_registrations_are_limited_per_network(client, sent_emails):
    for number in range(5):
        assert register(client, name=f"Player {number}").status_code == 201

    assert register(client, name="One Too Many").status_code == 429



# ---------- Execs reviewing registrations ----------

def first_registration_id():
    return saved_registrations()[0].registration_id


def test_execs_must_log_in_to_see_registrations(client, sent_emails):
    register(client)

    assert client.get("/registrations/").status_code == 401
    assert client.get("/registrations/pending-count").status_code == 401
    assert client.post(f"/registrations/{first_registration_id()}/approve").status_code == 401


def test_execs_see_pending_registrations(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()

    [registration] = client.get("/registrations/").json()

    assert registration["name"] == "Arjun Kumar"
    assert registration["status"] == "pending"
    assert client.get("/registrations/pending-count").json() == {"count": 1}


def test_approving_creates_the_player(client, make_exec, log_in, sent_emails):
    register(client)
    exec_user = make_exec()
    log_in()

    response = client.post(f"/registrations/{first_registration_id()}/approve")

    assert response.status_code == 200
    player = response.json()
    assert player["kica_id"] == "KICA001"
    assert player["name"] == "Arjun Kumar"
    assert player["parent_name"] == "Lakshmi Kumar"
    assert player["joined_on"] == kuwait_today().isoformat()

    [registration] = client.get("/registrations/", params={"show": "approved"}).json()
    assert registration["kica_id"] == "KICA001"
    assert registration["reviewed_by_name"] == exec_user.name
    assert client.get("/registrations/pending-count").json() == {"count": 0}


def test_approving_is_logged(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()

    client.post(f"/registrations/{first_registration_id()}/approve")

    with SessionLocal() as db:
        actions = [
            (entry.action, entry.table_name)
            for entry in db.scalars(select(AuditLog).order_by(AuditLog.audit_id))
        ]

    assert actions == [("CREATE", "players"), ("UPDATE", "player_registrations")]


def test_approved_player_gets_the_next_kica_id(client, make_exec, make_player, log_in, sent_emails):
    make_player(name="Yokshith", kica_id="KICA057")
    register(client)
    make_exec()
    log_in()

    response = client.post(f"/registrations/{first_registration_id()}/approve")

    assert response.json()["kica_id"] == "KICA058"


def test_cannot_approve_twice(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()
    registration_id = first_registration_id()

    client.post(f"/registrations/{registration_id}/approve")
    response = client.post(f"/registrations/{registration_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "This registration was already approved"


def test_approving_is_refused_if_the_player_was_added_meanwhile(
    client, make_exec, make_player, log_in, sent_emails
):
    register(client)
    make_player(name="Arjun Kumar")   # same name and birthday, added directly
    make_exec()
    log_in()

    response = client.post(f"/registrations/{first_registration_id()}/approve")

    assert response.status_code == 409


def test_rejecting_needs_a_reason(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()
    registration_id = first_registration_id()

    blank = client.post(f"/registrations/{registration_id}/reject", json={"reason": "   "})
    assert blank.status_code == 422

    response = client.post(
        f"/registrations/{registration_id}/reject",
        json={"reason": "Already a member under a different name"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["rejection_reason"] == "Already a member under a different name"
    assert client.get("/registrations/").json() == []
    assert len(client.get("/registrations/", params={"show": "rejected"}).json()) == 1


def test_rejected_registration_cannot_be_approved(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()
    registration_id = first_registration_id()

    client.post(f"/registrations/{registration_id}/reject", json={"reason": "Duplicate"})
    response = client.post(f"/registrations/{registration_id}/approve")

    assert response.status_code == 409
    assert response.json()["detail"] == "This registration was already rejected"


def test_family_can_register_again_after_a_rejection(client, make_exec, log_in, sent_emails):
    register(client)
    make_exec()
    log_in()
    client.post(f"/registrations/{first_registration_id()}/reject", json={"reason": "Wrong details"})

    assert register(client).status_code == 201


def test_unknown_registration(client, make_exec, log_in):
    make_exec()
    log_in()

    assert client.post("/registrations/999/approve").status_code == 404
