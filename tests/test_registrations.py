from datetime import timedelta

import pytest
from sqlalchemy import select

from club_time import kuwait_today
from database import SessionLocal
from models import PlayerRegistration


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
    assert "WhatsApp" in email["text"]


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