from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from audit import record_audit
from club_time import KUWAIT, kuwait_today
from dependencies import get_current_exec, get_db
from models import Exec, Transfer
from schemas import ExecOption, TransferCreate, TransferResponse, TransferReverse


router = APIRouter(
    prefix="/transfers",
    tags=["Transfers"],
    dependencies=[Depends(get_current_exec)]
)


def describe_transfers(db: Session, transfers: list[Transfer]) -> list[dict]:
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    return [
        {
            "transfer_id": t.transfer_id,
            "from_exec_id": t.from_exec_id,
            "from_exec_name": exec_names[t.from_exec_id],
            "to_exec_id": t.to_exec_id,
            "to_exec_name": exec_names[t.to_exec_id],
            "amount": t.amount,
            "transferred_on": t.transferred_at.astimezone(KUWAIT).date(),
            "status": t.status,
            "recorded_by_exec_id": t.recorded_by_exec_id,
            "recorded_by_name": exec_names[t.recorded_by_exec_id],
            "created_at": t.created_at
        }
        for t in transfers
    ]


@router.get("/other-execs", response_model=list[ExecOption])
def list_other_execs(
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    return db.scalars(
        select(Exec)
        .where(
            Exec.is_active.is_(True),
            Exec.approved_at.is_not(None),
            Exec.exec_id != current_exec.exec_id
        )
        .order_by(Exec.name)
    ).all()


@router.get("/", response_model=list[TransferResponse])
def list_transfers(db: Session = Depends(get_db)):
    transfers = db.scalars(
        select(Transfer).order_by(
            Transfer.transferred_at.desc(),
            Transfer.transfer_id.desc()
        )
    ).all()

    return describe_transfers(db, transfers)


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def record_transfer(
    transfer_data: TransferCreate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    if transfer_data.from_exec_id == current_exec.exec_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="You cannot transfer money to yourself"
        )

    sender = db.get(Exec, transfer_data.from_exec_id)

    if sender is None or not sender.is_active or sender.approved_at is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The giving Exec must be an active, approved Exec"
        )

    if transfer_data.transferred_on > kuwait_today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Transfer date cannot be in the future"
        )

    transfer = Transfer(
        from_exec_id=sender.exec_id,
        # The person receiving the money is the one who records it
        to_exec_id=current_exec.exec_id,
        amount=transfer_data.amount,
        transferred_at=datetime.combine(transfer_data.transferred_on, time(), tzinfo=KUWAIT),
        recorded_by_exec_id=current_exec.exec_id,
        status="active"
    )
    db.add(transfer)
    db.flush()

    record_audit(
        db, current_exec, "CREATE", "transfers", transfer.transfer_id,
        new_values={
            "from_exec_id": sender.exec_id,
            "to_exec_id": current_exec.exec_id,
            "amount": transfer.amount,
            "transferred_on": transfer_data.transferred_on
        }
    )

    db.commit()

    return describe_transfers(db, [transfer])[0]


@router.post("/{transfer_id}/reverse", response_model=TransferResponse)
def reverse_transfer(
    transfer_id: int,
    reversal: TransferReverse,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # Lock the row, so two people can't reverse it at the same moment
    transfer = db.get(Transfer, transfer_id, with_for_update=True)

    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )

    if current_exec.role != "admin" and transfer.recorded_by_exec_id != current_exec.exec_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reverse transfers you recorded"
        )

    if transfer.status == "reversed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This transfer has already been reversed"
        )

    transfer.status = "reversed"

    record_audit(
        db, current_exec, "REVERSE", "transfers", transfer.transfer_id,
        old_values={"status": "active"},
        new_values={"status": "reversed", "reason": reversal.reason.strip()}
    )

    db.commit()

    return describe_transfers(db, [transfer])[0]