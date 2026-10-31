from datetime import date
from decimal import Decimal

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from models import Attendance, ClubSession, FeeAdjustment, FeeRate, Player

ZERO = Decimal("0.000")


def month_start(day: date) -> date:
    return day.replace(day=1)


def get_monthly_rate(db: Session, fee_month: date) -> Decimal:
    # The newest rate that had already started by this month
    rate = db.scalar(
        select(FeeRate.monthly_amount)
        .where(FeeRate.effective_from <= fee_month)
        .order_by(FeeRate.effective_from.desc())
        .limit(1)
    )

    if rate is None:
        raise RuntimeError(f"No fee rate is set for {fee_month:%B %Y}")

    return rate


def monthly_fees(
    db: Session,
    player_id: int | None = None,
    fee_month: date | None = None
) -> list[dict]:
    session_month = cast(func.date_trunc("month", ClubSession.session_date), Date)

    # Each (player, month) where the player was present at least once
    attended = (
        select(Attendance.player_id, session_month)
        .join(ClubSession, ClubSession.session_id == Attendance.session_id)
        .where(Attendance.is_present.is_(True))
        .distinct()
    )

    # Total of all adjustments for each (player, month)
    adjustments = (
        select(
            FeeAdjustment.player_id,
            FeeAdjustment.fee_month,
            func.sum(FeeAdjustment.amount_change)
        )
        .group_by(FeeAdjustment.player_id, FeeAdjustment.fee_month)
    )

    if player_id is not None:
        attended = attended.where(Attendance.player_id == player_id)
        adjustments = adjustments.where(FeeAdjustment.player_id == player_id)

    if fee_month is not None:
        attended = attended.where(session_month == fee_month)
        adjustments = adjustments.where(FeeAdjustment.fee_month == fee_month)

    attended_months = {(pid, month) for pid, month in db.execute(attended)}
    adjustment_totals = {(pid, month): total for pid, month, total in db.execute(adjustments)}

    all_keys = attended_months | set(adjustment_totals)

    if not all_keys:
        return []

    player_names = dict(
        db.execute(
            select(Player.player_id, Player.name)
            .where(Player.player_id.in_({pid for pid, _ in all_keys}))
        ).all()
    )

    rates = {}
    fees = []

    for pid, month in all_keys:
        if month not in rates:
            rates[month] = get_monthly_rate(db, month)

        base_fee = rates[month] if (pid, month) in attended_months else ZERO
        adjustment_total = adjustment_totals.get((pid, month), ZERO)

        fees.append({
            "player_id": pid,
            "player_name": player_names[pid],
            "fee_month": month,
            "base_fee": base_fee,
            "adjustments": adjustment_total,
            "amount_due": max(base_fee + adjustment_total, ZERO)
        })

    fees.sort(key=lambda fee: (fee["player_name"], fee["fee_month"]))

    return fees
