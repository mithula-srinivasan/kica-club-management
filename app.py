from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Player

app = FastAPI()


# Defines the information required to add a player
class PlayerCreate(BaseModel):
    name: str


# Provides a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/players")
def create_player(
    player: PlayerCreate,
    db: Session = Depends(get_db)
):
    new_player = Player(name=player.name)

    db.add(new_player)
    db.commit()
    db.refresh(new_player)

    return {
        "player_id": new_player.player_id,
        "name": new_player.name,
        "is_active": new_player.is_active
    }