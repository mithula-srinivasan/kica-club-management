from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from balances import all_player_balances, cash_held_by_exec, month_summary, unpaid_for_month
from club_time import kuwait_today
from dependencies import get_current_exec, get_db
from fees import ZERO, month_start
from models import Player
from schemas import DashboardResponse, PlayerOutstanding


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_exec)]
)


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    month: date | None = None,
    db: Session = Depends(get_db)
):
    fee_month = month_start(month or kuwait_today())

    cash_held = cash_held_by_exec(db)
    balances = all_player_balances(db)

    active_players = db.scalar(
        select(func.count())
        .select_from(Player)
        .where(Player.is_active.is_(True))
    )

    return {
        "active_players": active_players,
        "club_balance": sum((row["amount"] for row in cash_held), ZERO),
        "cash_held": cash_held,
        "total_outstanding": sum((row["outstanding"] for row in balances), ZERO),
        "players_owing": sum(1 for row in balances if row["outstanding"] > 0),
        "total_credit": sum((row["credit"] for row in balances), ZERO),
        "month": month_summary(db, fee_month)
    }


@router.get("/outstanding", response_model=list[PlayerOutstanding])
def get_outstanding(db: Session = Depends(get_db)):
    owing = [row for row in all_player_balances(db) if row["outstanding"] > 0]

    # Biggest amount first; players owing the same amount in name order
    owing.sort(key=lambda row: (-row["outstanding"], row["player_name"]))

    return owing


@router.get("/unpaid", response_model=list[PlayerOutstanding])
def get_unpaid_for_month(
    month: date,
    db: Session = Depends(get_db)
):
    return unpaid_for_month(db, month_start(month))