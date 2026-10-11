from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy.exc import IntegrityError
from schemas import PlayerCreate, PlayerResponse, PlayerUpdate
from database import SessionLocal
from models import Player


router = APIRouter(
    prefix="/players",
    tags=["Players"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


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

    players = db.scalars(statement).all()

    return players


@router.post("/", response_model=PlayerResponse, status_code=201)
def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db)
):
    # Remove accidental spaces
    name = player.name.strip()
    kica_id = player.kica_id.strip()

    # Prevent empty names or IDs
    if not name or not kica_id:
        raise HTTPException(
            status_code=422,
            detail="Name and KICA ID cannot be empty"
        )

    # Check whether the KICA ID already exists
    existing_player = db.scalar(
        select(Player).where(Player.kica_id == kica_id)
    )

    if existing_player is not None:
        raise HTTPException(
            status_code=409,
            detail="This KICA ID is already registered"
        )

    # Create the new player
    new_player = Player(
        name=name,
        kica_id=kica_id,
        joined_on=player.joined_on,
        is_active=True
    )

    db.add(new_player)

    try:
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
    db: Session = Depends(get_db)
):
    # 1. Find the existing player
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    # 2. Get only the fields the Exec wants to change
    changes = updates.model_dump(exclude_unset=True)

    # 3. Validate the supplied values
    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null"
            )

        if field in ("name", "kica_id"):
            value = value.strip()

            if not value:
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} cannot be empty"
                )

        # 4. Apply each change to the player object
        setattr(player, field, value)

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
    db: Session = Depends(get_db)
):
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    player.is_active = is_active

    db.commit()
    db.refresh(player)

    return player