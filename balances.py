from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fees import ZERO, monthly_fees
from models import Payment, Player


def total_paid(db: Session, player_id: int) -> Decimal:
    total = db.scalar(
        select(func.sum(Payment.amount))
        .where(Payment.player_id == player_id, Payment.status == "active")
    )

    return total or ZERO


def player_statement(db: Session, player: Player) -> dict:
    fees = monthly_fees(db, player_id=player.player_id)
    paid = total_paid(db, player.player_id)

    # Apply everything paid to the oldest fees first
    unapplied = paid
    months = []

    for fee in fees:
        applied = min(fee["amount_due"], unapplied)
        unapplied -= applied

        months.append({
            "fee_month": fee["fee_month"],
            "amount_due": fee["amount_due"],
            "amount_paid": applied,
            "remaining": fee["amount_due"] - applied
        })

    total_due = sum((fee["amount_due"] for fee in fees), ZERO)

    return {
        "player_id": player.player_id,
        "player_name": player.name,
        "total_due": total_due,
        "total_paid": paid,
        "outstanding": total_due - (paid - unapplied),
        "credit": unapplied,
        "months": months
    }