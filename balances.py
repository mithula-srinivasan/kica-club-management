from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fees import ZERO, monthly_fees
from models import ClubSession, Exec, Expense, Payment, Player, Transfer


def total_paid(db: Session, player_id: int) -> Decimal:
    total = db.scalar(
        select(func.sum(Payment.amount))
        .where(Payment.player_id == player_id, Payment.status == "active")
    )

    return total or ZERO


def paid_by_player(db: Session) -> dict:
    return dict(
        db.execute(
            select(Payment.player_id, func.sum(Payment.amount))
            .where(Payment.status == "active")
            .group_by(Payment.player_id)
        ).all()
    )


def apply_oldest_first(fees: list[dict], paid: Decimal) -> tuple[list[dict], Decimal]:
    # Spread the money paid across the fees, oldest month first
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

    return months, unapplied


def player_statement(db: Session, player: Player) -> dict:
    fees = monthly_fees(db, player_id=player.player_id)
    paid = total_paid(db, player.player_id)

    # Apply everything paid to the oldest fees first
    months, unapplied = apply_oldest_first(fees, paid)

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



def cash_held_by_exec(db: Session) -> list[dict]:
    held = defaultdict(lambda: ZERO)

    # Money in: payments each Exec collected
    for exec_id, total in db.execute(
        select(Payment.collected_by_exec_id, func.sum(Payment.amount))
        .where(Payment.status == "active")
        .group_by(Payment.collected_by_exec_id)
    ):
        held[exec_id] += total

    # Money out: expenses each Exec paid
    for exec_id, total in db.execute(
        select(Expense.paid_by_exec_id, func.sum(Expense.amount))
        .where(Expense.status == "active")
        .group_by(Expense.paid_by_exec_id)
    ):
        held[exec_id] -= total

    # Money handed over: received adds, given subtracts
    for exec_id, total in db.execute(
        select(Transfer.to_exec_id, func.sum(Transfer.amount))
        .where(Transfer.status == "active")
        .group_by(Transfer.to_exec_id)
    ):
        held[exec_id] += total

    for exec_id, total in db.execute(
        select(Transfer.from_exec_id, func.sum(Transfer.amount))
        .where(Transfer.status == "active")
        .group_by(Transfer.from_exec_id)
    ):
        held[exec_id] -= total

    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    cash_held = [
        {"exec_id": exec_id, "name": exec_names[exec_id], "amount": amount}
        for exec_id, amount in held.items()
        if amount != 0
    ]
    cash_held.sort(key=lambda row: row["name"])

    return cash_held


def all_player_balances(db: Session) -> list[dict]:
    total_due = defaultdict(lambda: ZERO)

    for fee in monthly_fees(db):
        total_due[fee["player_id"]] += fee["amount_due"]

    total_paid = paid_by_player(db)

    player_ids = set(total_due) | set(total_paid)

    if not player_ids:
        return []

    player_names = dict(
        db.execute(
            select(Player.player_id, Player.name)
            .where(Player.player_id.in_(player_ids))
        ).all()
    )

    balances = []

    for player_id in player_ids:
        due = total_due[player_id]
        paid = total_paid.get(player_id, ZERO)
        covered = min(due, paid)

        balances.append({
            "player_id": player_id,
            "player_name": player_names[player_id],
            "total_due": due,
            "total_paid": paid,
            "outstanding": due - covered,
            "credit": paid - covered
        })

    balances.sort(key=lambda row: row["player_name"])

    return balances


def month_summary(db: Session, fee_month: date) -> dict:
    next_month = (fee_month + timedelta(days=32)).replace(day=1)

    fees = monthly_fees(db, fee_month=fee_month)

    sessions_held = db.scalar(
        select(func.count())
        .select_from(ClubSession)
        .where(
            ClubSession.session_date >= fee_month,
            ClubSession.session_date < next_month
        )
    )

    payments_received = db.scalar(
        select(func.sum(Payment.amount))
        .where(
            Payment.status == "active",
            Payment.paid_on >= fee_month,
            Payment.paid_on < next_month
        )
    )

    expenses_paid = db.scalar(
        select(func.sum(Expense.amount))
        .where(
            Expense.status == "active",
            Expense.expense_date >= fee_month,
            Expense.expense_date < next_month
        )
    )

    return {
        "month": fee_month,
        "sessions_held": sessions_held,
        "players_attended": sum(1 for fee in fees if fee["base_fee"] > 0),
        "fees_assessed": sum((fee["amount_due"] for fee in fees), ZERO),
        "payments_received": payments_received or ZERO,
        "expenses_paid": expenses_paid or ZERO
    }


def unpaid_for_month(db: Session, fee_month: date) -> list[dict]:
    fees_by_player = defaultdict(list)

    for fee in monthly_fees(db):
        fees_by_player[fee["player_id"]].append(fee)

    total_paid = paid_by_player(db)
    unpaid = []

    for player_id, fees in fees_by_player.items():
        months, _ = apply_oldest_first(fees, total_paid.get(player_id, ZERO))

        for month in months:
            if month["fee_month"] == fee_month and month["remaining"] > 0:
                unpaid.append({
                    "player_id": player_id,
                    "player_name": fees[0]["player_name"],
                    "outstanding": month["remaining"]
                })

    unpaid.sort(key=lambda row: row["player_name"])

    return unpaid