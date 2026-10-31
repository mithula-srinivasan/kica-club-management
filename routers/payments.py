from club_time import kuwait_today
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit import record_audit
from balances import player_statement
from dependencies import get_current_exec, get_db
from models import Exec, Payment, Player
from schemas import (
    PaymentCreate,
    PaymentResponse,
    PaymentReverse,
    PlayerStatement,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(get_current_exec)]
)


def describe_payments(db: Session, payments: list[Payment]) -> list[dict]:
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())
    player_names = dict(
        db.execute(
            select(Player.player_id, Player.name)
            .where(Player.player_id.in_({p.player_id for p in payments}))
        ).all()
    )

    return [
        {
            "payment_id": p.payment_id,
            "player_id": p.player_id,
            "player_name": player_names[p.player_id],
            "amount": p.amount,
            "paid_on": p.paid_on,
            "method": p.method,
            "note": p.note,
            "status": p.status,
            "recorded_by_exec_id": p.recorded_by_exec_id,
            "recorded_by_name": exec_names[p.recorded_by_exec_id],
            "created_at": p.created_at
        }
        for p in payments
    ]


def find_by_key(db: Session, idempotency_key: str | None) -> Payment | None:
    if not idempotency_key:
        return None

    return db.scalar(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )



@router.get("/", response_model=list[PaymentResponse])
def list_payments(
    player_id: int | None = None,
    db: Session = Depends(get_db)
):
    statement = select(Payment).order_by(
        Payment.paid_on.desc(),
        Payment.payment_id.desc()
    )

    if player_id is not None:
        statement = statement.where(Payment.player_id == player_id)

    return describe_payments(db, db.scalars(statement).all())


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payment_data: PaymentCreate,
    response: Response,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # Same form submitted again: return the payment already recorded
    existing = find_by_key(db, payment_data.idempotency_key)

    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return describe_payments(db, [existing])[0]

    if db.get(Player, payment_data.player_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )


    if payment_data.paid_on > kuwait_today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Payment date cannot be in the future"
        )

    payment = Payment(
        player_id=payment_data.player_id,
        amount=payment_data.amount,
        paid_on=payment_data.paid_on,
        method=payment_data.method,
        note=(payment_data.note or "").strip() or None,
        # The person recording the payment is always the one who collected it
        collected_by_exec_id=current_exec.exec_id,
        recorded_by_exec_id=current_exec.exec_id,
        status="active",
        idempotency_key=payment_data.idempotency_key
    )
    db.add(payment)

    try:
        db.flush()

        record_audit(
            db, current_exec, "CREATE", "payments", payment.payment_id,
            new_values={
                "player_id": payment.player_id,
                "amount": payment.amount,
                "paid_on": payment.paid_on,
                "method": payment.method,
                "collected_by_exec_id": current_exec.exec_id
            }
        )

        db.commit()
    except IntegrityError:
        db.rollback()

        # The same form was submitted twice at the same moment
        existing = find_by_key(db, payment_data.idempotency_key)

        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The payment could not be recorded"
            )

        response.status_code = status.HTTP_200_OK
        return describe_payments(db, [existing])[0]

    return describe_payments(db, [payment])[0]


@router.post("/{payment_id}/reverse", response_model=PaymentResponse)
def reverse_payment(
    payment_id: int,
    reversal: PaymentReverse,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # Lock the row, so two people can't reverse it at the same moment
    payment = db.get(Payment, payment_id, with_for_update=True)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if current_exec.role != "admin" and payment.recorded_by_exec_id != current_exec.exec_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reverse payments you recorded"
        )

    if payment.status == "reversed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment has already been reversed"
        )

    payment.status = "reversed"

    record_audit(
        db, current_exec, "REVERSE", "payments", payment.payment_id,
        old_values={"status": "active"},
        new_values={"status": "reversed", "reason": reversal.reason.strip()}
    )

    db.commit()

    return describe_payments(db, [payment])[0]


@router.get("/players/{player_id}/statement", response_model=PlayerStatement)
def get_player_statement(
    player_id: int,
    db: Session = Depends(get_db)
):
    player = db.get(Player, player_id)

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )

    return player_statement(db, player)