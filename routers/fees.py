from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from club_time import kuwait_today
from models import Exec, FeeAdjustment, FeeRate, Player
from schemas import FeeAdjustmentCreate, FeeRateCreate, FeeRateResponse, MonthlyFeeResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from audit import record_audit
from dependencies import get_current_exec, get_db, require_admin
from fees import ZERO, month_start, monthly_fees

from datetime import date


router = APIRouter(
    prefix="/fees",
    tags=["Fees"],
    dependencies=[Depends(get_current_exec)]
)


@router.get("/players/{player_id}", response_model=list[MonthlyFeeResponse])
def get_player_fees(
    player_id: int,
    db: Session = Depends(get_db)
):
    if db.get(Player, player_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    return monthly_fees(db, player_id=player_id)


@router.get("/month", response_model=list[MonthlyFeeResponse])
def get_month_fees(
    month: date,
    db: Session = Depends(get_db)
):
    return monthly_fees(db, fee_month=month_start(month))


@router.post(
    "/adjustments",
    response_model=MonthlyFeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_fee_adjustment(
    adjustment: FeeAdjustmentCreate,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if db.get(Player, adjustment.player_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    if adjustment.amount_change == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Adjustment amount cannot be zero"
        )

    fee_month = month_start(adjustment.fee_month)

    # The fee before this adjustment, without the "never below zero" rule
    [current] = monthly_fees(db, player_id=adjustment.player_id, fee_month=fee_month) or [None]
    current_total = current["base_fee"] + current["adjustments"] if current else ZERO

    if current_total + adjustment.amount_change < 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This adjustment would make the fee negative"
        )

    new_adjustment = FeeAdjustment(
        player_id=adjustment.player_id,
        fee_month=fee_month,
        amount_change=adjustment.amount_change,
        reason=adjustment.reason.strip(),
        adjusted_by_exec_id=current_admin.exec_id
    )
    db.add(new_adjustment)
    db.flush()

    record_audit(
        db, current_admin, "CREATE", "fee_adjustments", new_adjustment.adjustment_id,
        new_values={
            "player_id": adjustment.player_id,
            "fee_month": fee_month,
            "amount_change": adjustment.amount_change,
            "reason": new_adjustment.reason
        }
    )

    db.commit()

    [updated] = monthly_fees(db, player_id=adjustment.player_id, fee_month=fee_month)

    return updated



def describe_rates(db: Session, rates: list[FeeRate]) -> list[dict]:
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    return [
        {
            "fee_rate_id": rate.fee_rate_id,
            "monthly_amount": rate.monthly_amount,
            "effective_from": rate.effective_from,
            "changed_by_name": exec_names.get(rate.changed_by_exec_id),
        }
        for rate in rates
    ]


@router.get("/rates", response_model=list[FeeRateResponse])
def list_fee_rates(db: Session = Depends(get_db)):
    rates = db.scalars(select(FeeRate).order_by(FeeRate.effective_from.desc())).all()

    return describe_rates(db, rates)


@router.post(
    "/rates",
    response_model=FeeRateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_fee_rate(
    rate_data: FeeRateCreate,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    effective_from = month_start(rate_data.effective_from)

    # Past months keep the rate they were charged at
    if effective_from < month_start(kuwait_today()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A new rate can only start from this month or a later month"
        )

    rate = FeeRate(
        monthly_amount=rate_data.monthly_amount,
        effective_from=effective_from,
        changed_by_exec_id=current_admin.exec_id
    )
    db.add(rate)

    try:
        db.flush()

        record_audit(
            db, current_admin, "CREATE", "fee_rates", rate.fee_rate_id,
            new_values={
                "monthly_amount": rate.monthly_amount,
                "effective_from": effective_from
            }
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A rate already starts in that month"
        )

    return describe_rates(db, [rate])[0]


@router.delete("/rates/{fee_rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee_rate(
    fee_rate_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    rate = db.get(FeeRate, fee_rate_id)

    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fee rate not found"
        )

    # Members may already have been charged at a rate that has started
    if rate.effective_from <= month_start(kuwait_today()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This rate has already started and cannot be removed"
        )

    record_audit(
        db, current_admin, "DELETE", "fee_rates", fee_rate_id,
        old_values={
            "monthly_amount": rate.monthly_amount,
            "effective_from": rate.effective_from
        }
    )

    db.delete(rate)
    db.commit()