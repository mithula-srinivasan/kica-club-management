import re

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from club_time import kuwait_today
from models import Player, PlayerRegistration
from countries import ALLOWED_COUNTRIES


# Fields every player must have, with the name shown in error messages.
# (The KICA ID is not here: it is given automatically and cannot be changed.)
# Fields every player must have, with the name shown in error messages.
# (The KICA ID is not here: it is given automatically and cannot be changed.)
REQUIRED_FIELDS = {
    "name": "Name",
    "phone_1": "Phone 1",
    "email": "Email",
    "date_of_birth": "Date of birth",
    "parent_name": "Parent name",
    "country": "Country",
    "gender": "Gender",
}

DUPLICATE_MESSAGE = "A player with this name and date of birth is already registered."

# "KICA" followed by digits, e.g. KICA057
KICA_ID_FORMAT = re.compile(r"KICA(\d+)")


def clean(value):
    """Tidy text: trim the ends and turn repeated spaces into one ("  Arjun   Kumar " -> "Arjun Kumar").
    Blank text becomes None. Other values (dates, numbers) are unchanged."""
    if isinstance(value, str):
        value = " ".join(value.split())
        return value or None
    return value


def check_date_of_birth(date_of_birth):
    if date_of_birth is not None and date_of_birth > kuwait_today():
        raise HTTPException(
            status_code=422,
            detail="Date of birth cannot be in the future"
        )



def check_country(country):
    if country not in ALLOWED_COUNTRIES:
        raise HTTPException(
            status_code=422,
            detail="Please choose a country from the list"
        )


def next_kica_id(db: Session) -> str:
    """The next KICA ID: the highest number used so far + 1, e.g. KICA058."""
    highest = 0

    for kica_id in db.scalars(select(Player.kica_id)):
        match = KICA_ID_FORMAT.fullmatch(kica_id)

        if match:
            highest = max(highest, int(match.group(1)))

    return f"KICA{highest + 1:03d}"


def lock_player_tables(db: Session):
    """Make anyone else adding a player or registration wait until we save.
    Stops two people creating the same KICA ID or the same player at the same moment.
    Reading is not blocked."""
    db.execute(text("LOCK TABLE players, player_registrations IN EXCLUSIVE MODE"))


def name_and_dob_taken(
    db: Session,
    name,
    date_of_birth,
    ignore_player_id=None,
    ignore_registration_id=None
) -> bool:
    """True if a player, or a registration waiting for approval, already has
    this name (ignoring capitals) and date of birth."""
    player_query = select(Player.player_id).where(
        func.lower(Player.name) == name.lower(),
        Player.date_of_birth == date_of_birth
    )

    # When editing a player, they shouldn't count as their own duplicate
    if ignore_player_id is not None:
        player_query = player_query.where(Player.player_id != ignore_player_id)

    if db.scalar(player_query.limit(1)) is not None:
        return True

    pending_query = select(PlayerRegistration.registration_id).where(
        func.lower(PlayerRegistration.name) == name.lower(),
        PlayerRegistration.date_of_birth == date_of_birth,
        PlayerRegistration.status == "pending"
    )

    # When approving a registration, it shouldn't count as its own duplicate
    if ignore_registration_id is not None:
        pending_query = pending_query.where(
            PlayerRegistration.registration_id != ignore_registration_id
        )

    return db.scalar(pending_query.limit(1)) is not None