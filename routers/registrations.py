from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from audit import record_audit
from club_time import kuwait_today
from config import setting
from dependencies import get_current_exec, get_db
from email_service import send_email
from models import Exec, Player, PlayerRegistration
from player_rules import (
    DUPLICATE_MESSAGE,
    REQUIRED_FIELDS,
    check_date_of_birth,
    clean,
    lock_player_tables,
    name_and_dob_taken,
    next_kica_id,
    check_country
)
from rate_limit import (
    REGISTRATION_LIMIT_PER_IP,
    REGISTRATION_MESSAGE,
    REGISTRATION_WINDOW,
    check_rate_limit,
    client_ip,
    record_hit,
)
from schemas import (
    PlayerDetails,
    PlayerResponse,
    RegistrationCreate,
    RegistrationReject,
    RegistrationResponse,
)


# How parents can reach the club, e.g. kica.chesskwt@gmail.com. Required in production.
CLUB_CONTACT = setting("CLUB_CONTACT", "kica.chesskwt@gmail.com")

# Submitting is public (no login). Every other route below asks for an Exec login itself.
router = APIRouter(
    prefix="/registrations",
    tags=["Registrations"]
)

THANK_YOU = {"message": "Thank you! We have received your registration."}

# The player details a registration carries over to the new player:
# name, parent_name, phone_1, phone_2, email, date_of_birth, gender, fide_id
PLAYER_DETAIL_FIELDS = list(PlayerDetails.model_fields)


def thank_you_email(parent_name: str, player_name: str) -> str:
    return (
        f"Dear {parent_name},\n\n"
        f"Thank you for registering {player_name} with the Kuwait Indian Chess Association (KICA)!\n\n"
        "We have received your registration. "
        "A member of our team will review it and contact you soon.\n\n"
        f"If you have any questions, please contact us at {CLUB_CONTACT}.\n\n"
        "Warm regards,\n"
        "Kuwait Indian Chess Association"
    )


def describe_registrations(db: Session, registrations: list[PlayerRegistration]) -> list[dict]:
    """Registrations as Execs see them, with names instead of ID numbers."""
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())
    kica_ids = dict(db.execute(select(Player.player_id, Player.kica_id)).all())

    return [
        {
            "registration_id": r.registration_id,
            "name": r.name,
            "parent_name": r.parent_name,
            "phone_1": r.phone_1,
            "phone_2": r.phone_2,
            "email": r.email,
            "date_of_birth": r.date_of_birth,
            "country": r.country,
            "gender": r.gender,
            "fide_id": r.fide_id,
            "status": r.status,
            "submitted_at": r.submitted_at,
            "consented_at": r.consented_at,
            "reviewed_at": r.reviewed_at,
            "reviewed_by_name": exec_names.get(r.reviewed_by_exec_id),
            "rejection_reason": r.rejection_reason,
            "player_id": r.player_id,
            "kica_id": kica_ids.get(r.player_id),
        }
        for r in registrations
    ]


def find_pending(db: Session, registration_id: int) -> PlayerRegistration:
    """The registration, if it exists and is still waiting. Otherwise a clear error."""
    registration = db.get(PlayerRegistration, registration_id)

    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    if registration.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"This registration was already {registration.status}"
        )

    return registration


# ---------- Public: the "Join KICA" form ----------

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
    check_country(details["country"])

    # 5. Refuse a player (or waiting registration) with the same name and date of birth
    lock_player_tables(db)

    if name_and_dob_taken(db, details["name"], details["date_of_birth"]):
        raise HTTPException(
            status_code=409,
            detail=f"{DUPLICATE_MESSAGE} If you think this is a mistake, "
                   f"please contact us at {CLUB_CONTACT}."
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


# ---------- Execs only: review registrations ----------

@router.get(
    "/",
    response_model=list[RegistrationResponse],
    dependencies=[Depends(get_current_exec)]
)
def list_registrations(
    show: Literal["pending", "approved", "rejected"] = "pending",
    db: Session = Depends(get_db)
):
    statement = select(PlayerRegistration).where(PlayerRegistration.status == show)

    if show == "pending":
        # Oldest first, so the ones waiting longest are dealt with first
        statement = statement.order_by(PlayerRegistration.submitted_at)
    else:
        # Most recently reviewed first
        statement = statement.order_by(PlayerRegistration.reviewed_at.desc())

    return describe_registrations(db, db.scalars(statement).all())


@router.get("/pending-count", dependencies=[Depends(get_current_exec)])
def count_pending(db: Session = Depends(get_db)):
    count = db.scalar(
        select(func.count())
        .select_from(PlayerRegistration)
        .where(PlayerRegistration.status == "pending")
    )

    return {"count": count}


@router.post("/{registration_id}/approve", response_model=PlayerResponse)
def approve_registration(
    registration_id: int,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # 1. Lock first: if two Execs click Approve at once, the second waits,
    #    then sees it's already approved
    lock_player_tables(db)

    registration = find_pending(db, registration_id)

    # 2. Someone may have added this player since the form was sent
    if name_and_dob_taken(
        db,
        registration.name,
        registration.date_of_birth,
        ignore_registration_id=registration.registration_id
    ):
        raise HTTPException(status_code=409, detail=DUPLICATE_MESSAGE)

    # 3. Create the player from the registration's details
    details = {field: getattr(registration, field) for field in PLAYER_DETAIL_FIELDS}
    details["kica_id"] = next_kica_id(db)
    details["joined_on"] = kuwait_today()

    player = Player(**details, is_active=True)
    db.add(player)
    db.flush()

    # 4. Mark the registration as approved, linked to the new player
    registration.status = "approved"
    registration.reviewed_at = datetime.now(timezone.utc)
    registration.reviewed_by_exec_id = current_exec.exec_id
    registration.player_id = player.player_id

    # 5. Log both: the new player, and the registration changing
    record_audit(
        db, current_exec, "CREATE", "players", player.player_id,
        new_values={
            **details,
            "is_active": True,
            "registration_id": registration.registration_id
        }
    )

    record_audit(
        db, current_exec, "UPDATE", "player_registrations", registration.registration_id,
        old_values={"status": "pending"},
        new_values={"status": "approved", "player_id": player.player_id}
    )

    db.commit()
    db.refresh(player)

    return player


@router.post("/{registration_id}/reject", response_model=RegistrationResponse)
def reject_registration(
    registration_id: int,
    rejection: RegistrationReject,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    reason = rejection.reason.strip()

    if not reason:
        raise HTTPException(status_code=422, detail="Please give a reason for rejecting")

    # Same lock as approving, so the two can't happen at the same moment
    lock_player_tables(db)

    registration = find_pending(db, registration_id)

    registration.status = "rejected"
    registration.rejection_reason = reason
    registration.reviewed_at = datetime.now(timezone.utc)
    registration.reviewed_by_exec_id = current_exec.exec_id

    record_audit(
        db, current_exec, "UPDATE", "player_registrations", registration.registration_id,
        old_values={"status": "pending"},
        new_values={"status": "rejected", "rejection_reason": reason}
    )

    db.commit()

    return describe_registrations(db, [registration])[0]