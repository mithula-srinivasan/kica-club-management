from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit import record_audit
from club_time import kuwait_today
from dependencies import get_db, require_admin
from models import Exec, ExecOpeningBalance, Player, PlayerOpeningBalance
from schemas import (
    ExecOpeningBalanceResponse,
    ExecOpeningBalanceSet,
    OpeningBalancesResponse,
    PlayerOpeningBalanceResponse,
    PlayerOpeningBalanceSet,
)


router = APIRouter(
    prefix="/opening-balances",
    tags=["Opening balances"],
    dependencies=[Depends(require_admin)]
)


def exec_names(db: Session) -> dict:
    return dict(db.execute(select(Exec.exec_id, Exec.name)).all())


def describe_exec_opening(row: ExecOpeningBalance, names: dict) -> dict:
    return {
        "exec_id": row.exec_id,
        "name": names[row.exec_id],
        "amount": row.amount,
        "as_of": row.as_of,
        "set_by_name": names[row.set_by_exec_id],
        "updated_at": row.updated_at
    }


def describe_player_opening(row: PlayerOpeningBalance, player_name: str, names: dict) -> dict:
    return {
        "player_id": row.player_id,
        "player_name": player_name,
        "amount": row.amount,
        "as_of": row.as_of,
        "set_by_name": names[row.set_by_exec_id],
        "updated_at": row.updated_at
    }


def check_not_future(as_of) -> None:
    if as_of > kuwait_today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The 'as of' date cannot be in the future"
        )


def save_or_conflict(db: Session) -> None:
    # Two admins setting the same opening balance at the same moment
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This opening balance was changed at the same time. Please try again."
        )


@router.get("/", response_model=OpeningBalancesResponse)
def list_opening_balances(db: Session = Depends(get_db)):
    names = exec_names(db)

    exec_rows = db.scalars(select(ExecOpeningBalance)).all()
    player_rows = db.execute(
        select(PlayerOpeningBalance, Player.name)
        .join(Player, Player.player_id == PlayerOpeningBalance.player_id)
        .order_by(Player.name)
    ).all()

    execs = [describe_exec_opening(row, names) for row in exec_rows]
    execs.sort(key=lambda row: row["name"])

    return {
        "execs": execs,
        "players": [
            describe_player_opening(row, player_name, names)
            for row, player_name in player_rows
        ]
    }


@router.put("/execs/{exec_id}", response_model=ExecOpeningBalanceResponse)
def set_exec_opening_balance(
    exec_id: int,
    opening: ExecOpeningBalanceSet,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = db.get(Exec, exec_id)

    if exec_user is None or exec_user.approved_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exec not found"
        )

    check_not_future(opening.as_of)

    row = db.get(ExecOpeningBalance, exec_id)
    new_values = {"amount": opening.amount, "as_of": opening.as_of}

    if row is None:
        row = ExecOpeningBalance(
            exec_id=exec_id,
            amount=opening.amount,
            as_of=opening.as_of,
            set_by_exec_id=current_admin.exec_id
        )
        db.add(row)
        record_audit(
            db, current_admin, "CREATE", "exec_opening_balances", exec_id,
            new_values=new_values
        )
    else:
        old_values = {"amount": row.amount, "as_of": row.as_of}
        row.amount = opening.amount
        row.as_of = opening.as_of
        row.set_by_exec_id = current_admin.exec_id
        record_audit(
            db, current_admin, "UPDATE", "exec_opening_balances", exec_id,
            old_values=old_values,
            new_values=new_values
        )

    save_or_conflict(db)

    return describe_exec_opening(row, exec_names(db))


@router.put("/players/{player_id}", response_model=PlayerOpeningBalanceResponse)
def set_player_opening_balance(
    player_id: int,
    opening: PlayerOpeningBalanceSet,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    check_not_future(opening.as_of)

    row = db.get(PlayerOpeningBalance, player_id)
    new_values = {"amount": opening.amount, "as_of": opening.as_of}

    if row is None:
        row = PlayerOpeningBalance(
            player_id=player_id,
            amount=opening.amount,
            as_of=opening.as_of,
            set_by_exec_id=current_admin.exec_id
        )
        db.add(row)
        record_audit(
            db, current_admin, "CREATE", "player_opening_balances", player_id,
            new_values=new_values
        )
    else:
        old_values = {"amount": row.amount, "as_of": row.as_of}
        row.amount = opening.amount
        row.as_of = opening.as_of
        row.set_by_exec_id = current_admin.exec_id
        record_audit(
            db, current_admin, "UPDATE", "player_opening_balances", player_id,
            old_values=old_values,
            new_values=new_values
        )

    save_or_conflict(db)

    return describe_player_opening(row, player.name, exec_names(db))


@router.delete("/execs/{exec_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exec_opening_balance(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    row = db.get(ExecOpeningBalance, exec_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No opening balance for this Exec"
        )

    record_audit(
        db, current_admin, "DELETE", "exec_opening_balances", exec_id,
        old_values={"amount": row.amount, "as_of": row.as_of}
    )

    db.delete(row)
    db.commit()


@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player_opening_balance(
    player_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    row = db.get(PlayerOpeningBalance, player_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No opening balance for this player"
        )

    record_audit(
        db, current_admin, "DELETE", "player_opening_balances", player_id,
        old_values={"amount": row.amount, "as_of": row.as_of}
    )

    db.delete(row)
    db.commit()