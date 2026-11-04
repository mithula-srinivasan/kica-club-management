from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit import record_audit
from club_time import kuwait_today
from dependencies import get_current_exec, get_db
from models import Exec, Player
from schemas import PlayerCreate, PlayerResponse, PlayerUpdate


router = APIRouter(
    prefix="/players",
    tags=["Players"],
    dependencies=[Depends(get_current_exec)]
)

# Fields every player must have, with the name shown in error messages
REQUIRED_FIELDS = {
    "name": "Name",
    "kica_id": "KICA ID",
    "phone_1": "Phone 1",
    "email": "Email",
    "date_of_birth": "Date of birth",
    "parent_name": "Parent name",
}


def clean(value):
    """Trim spaces from text. Blank text becomes None. Other values are unchanged."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def check_date_of_birth(date_of_birth):
    if date_of_birth is not None and date_of_birth > kuwait_today():
        raise HTTPException(
            status_code=422,
            detail="Date of birth cannot be in the future"
        )


@router.get("/", response_model=list[PlayerResponse])
def get_players(
    search: str | None = None,
    db: Session = Depends(get_db)
):
    statement = select(Player)

    if search and search.strip():
        statement = statement.where(
            Player.name.ilike(f"%{search.strip()}%")
        )

    statement = statement.order_by(Player.name)

    return db.scalars(statement).all()


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


@router.post("/", response_model=PlayerResponse, status_code=201)
def create_player(
    player: PlayerCreate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # 1. Tidy every field: trim spaces, blank -> None
    details = {field: clean(value) for field, value in player.model_dump().items()}

    # 2. Required fields must not be blank (e.g. "   " for a name)
    for field, label in REQUIRED_FIELDS.items():
        if details[field] is None:
            raise HTTPException(status_code=422, detail=f"{label} is required")

    check_date_of_birth(details["date_of_birth"])

    # 3. The KICA ID must be unique
    existing_player = db.scalar(
        select(Player).where(Player.kica_id == details["kica_id"])
    )

    if existing_player is not None:
        raise HTTPException(
            status_code=409,
            detail="This KICA ID is already registered"
        )

    # 4. Create the player and log it
    new_player = Player(**details, is_active=True)
    db.add(new_player)

    try:
        # Send the INSERT now so the new player gets its player_id, without saving yet
        db.flush()

        record_audit(
            db, current_exec, "CREATE", "players", new_player.player_id,
            new_values={**details, "is_active": True}
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create player: a database constraint was violated"
        )

    db.refresh(new_player)

    return new_player


@router.patch("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    updates: PlayerUpdate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # 1. Find the existing player
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2. Only the fields the Exec actually sent
    changes = updates.model_dump(exclude_unset=True)

    old_values = {}
    new_values = {}

    for field, value in changes.items():
        value = clean(value)

        # 3. Required fields can be changed but not emptied.
        #    Optional fields can be emptied (blank -> None).
        if value is None and field in REQUIRED_FIELDS:
            raise HTTPException(
                status_code=422,
                detail=f"{REQUIRED_FIELDS[field]} cannot be empty"
            )

        if value is None and field == "joined_on":
            raise HTTPException(status_code=422, detail="Joined on cannot be empty")

        if field == "date_of_birth":
            check_date_of_birth(value)

        # 4. Remember what changed, then apply it
        if getattr(player, field) != value:
            old_values[field] = getattr(player, field)
            new_values[field] = value
            setattr(player, field, value)

    if new_values:
        record_audit(
            db, current_exec, "UPDATE", "players", player.player_id,
            old_values=old_values,
            new_values=new_values
        )

    # 5. Save the changes
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update player: KICA ID may already exist"
        )

    db.refresh(player)

    return player


@router.patch("/{player_id}/status", response_model=PlayerResponse)
def update_player_status(
    player_id: int,
    is_active: bool,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.is_active != is_active:
        record_audit(
            db, current_exec, "UPDATE", "players", player.player_id,
            old_values={"is_active": player.is_active},
            new_values={"is_active": is_active}
        )

    player.is_active = is_active

    db.commit()
    db.refresh(player)

    return player