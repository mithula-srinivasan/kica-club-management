from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from config import setting
from dependencies import get_db
from email_service import send_email
from models import PlayerRegistration
from player_rules import (
    DUPLICATE_MESSAGE,
    REQUIRED_FIELDS,
    check_date_of_birth,
    clean,
    lock_player_tables,
    name_and_dob_taken,
)
from rate_limit import (
    REGISTRATION_LIMIT_PER_IP,
    REGISTRATION_MESSAGE,
    REGISTRATION_WINDOW,
    check_rate_limit,
    client_ip,
    record_hit,
)
from schemas import RegistrationCreate


# The club's WhatsApp number, shown in the thank-you email. Required in production.
CLUB_WHATSAPP = setting("CLUB_WHATSAPP", "+965 0000 0000")

# No login needed: this is the public "Join KICA" form
router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"]
)

THANK_YOU = {"message": "Thank you! We have received your registration."}


def thank_you_email(parent_name: str, player_name: str) -> str:
    return (
        f"Dear {parent_name},\n\n"
        f"Thank you for registering {player_name} with the Kuwait Indian Chess Association (KICA)!\n\n"
        "We have received your registration. "
        "A member of our team will review it and contact you soon.\n\n"
        f"If you have any questions, please contact us on WhatsApp at {CLUB_WHATSAPP}.\n\n"
        "Warm regards,\n"
        "Kuwait Indian Chess Association"
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_registration(
    registration: RegistrationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. At most a few registrations per hour from the same network
    ip_key = f"registration-ip:{client_ip(request)}"
    check_rate_limit(db, ip_key, REGISTRATION_LIMIT_PER_IP, REGISTRATION_WINDOW, REGISTRATION_MESSAGE)
    record_hit(db, ip_key)
    db.commit()

    # 2. The hidden box was filled in, so this is a spam bot.
    #    Pretend it worked (so the bot doesn't try something else), but save nothing.
    if registration.website:
        return THANK_YOU

    # 3. The consent box must be ticked
    if not registration.consent:
        raise HTTPException(
            status_code=422,
            detail="Please tick the box to agree to the club rules"
        )

    # 4. The same checks as the exec "Add player" form
    details = {
        field: clean(value)
        for field, value in registration.model_dump(exclude={"consent", "website"}).items()
    }

    for field, label in REQUIRED_FIELDS.items():
        if details[field] is None:
            raise HTTPException(status_code=422, detail=f"{label} is required")

    check_date_of_birth(details["date_of_birth"])

    # 5. Refuse a player (or waiting registration) with the same name and date of birth
    lock_player_tables(db)

    if name_and_dob_taken(db, details["name"], details["date_of_birth"]):
        raise HTTPException(
            status_code=409,
            detail=f"{DUPLICATE_MESSAGE} If you think this is a mistake, "
                   f"please contact us on WhatsApp at {CLUB_WHATSAPP}."
        )

    # 6. Save it, waiting for an Exec to approve it
    db.add(
        PlayerRegistration(
            **details,
            status="pending",
            consented_at=datetime.now(timezone.utc)
        )
    )
    db.commit()

    # 7. Thank the parent (sent after the reply, so the form doesn't wait for Gmail)
    background_tasks.add_task(
        send_email,
        details["email"],
        "Thank you for registering with KICA",
        thank_you_email(details["parent_name"], details["name"])
    )

    return THANK_YOU