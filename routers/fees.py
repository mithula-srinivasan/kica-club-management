from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from audit import record_audit
from dependencies import get_current_exec, get_db, require_admin
from fees import ZERO, month_start, monthly_fees
from models import Exec, FeeAdjustment, Player
from schemas import FeeAdjustmentCreate, MonthlyFeeResponse

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