from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from audit import record_audit
from club_time import kuwait_today
from dependencies import choose_handler, get_current_exec, get_db
from models import Exec, Income
from schemas import IncomeCreate, IncomeResponse, IncomeReverse


router = APIRouter(
    prefix="/income",
    tags=["Income"],
    dependencies=[Depends(get_current_exec)]
)


def describe_income(db: Session, entries: list[Income]) -> list[dict]:
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    return [
        {
            "income_id": i.income_id,
            "description": i.description,
            "amount": i.amount,
            "income_date": i.income_date,
            "status": i.status,
            "received_by_exec_id": i.received_by_exec_id,
            "received_by_name": exec_names[i.received_by_exec_id],
            "recorded_by_exec_id": i.recorded_by_exec_id,
            "recorded_by_name": exec_names[i.recorded_by_exec_id],
            "created_at": i.created_at
        }
        for i in entries
    ]


@router.get("/", response_model=list[IncomeResponse])
def list_income(db: Session = Depends(get_db)):
    entries = db.scalars(
        select(Income).order_by(
            Income.income_date.desc(),
            Income.income_id.desc()
        )
    ).all()

    return describe_income(db, entries)


@router.post("/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def record_income(
    income_data: IncomeCreate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    if income_data.income_date > kuwait_today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Income date cannot be in the future"
        )

    description = income_data.description.strip()

    if not description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Description cannot be empty"
        )

    # Admins can record income that another Exec received
    receiver = choose_handler(db, current_exec, income_data.received_by_exec_id)

    income = Income(
        description=description,
        amount=income_data.amount,
        income_date=income_data.income_date,
        received_by_exec_id=receiver.exec_id,
        recorded_by_exec_id=current_exec.exec_id,
        status="active"
    )
    db.add(income)
    db.flush()

    record_audit(
        db, current_exec, "CREATE", "incomes", income.income_id,
        new_values={
            "description": description,
            "amount": income.amount,
            "income_date": income.income_date,
            "received_by_exec_id": receiver.exec_id
        }
    )

    db.commit()

    return describe_income(db, [income])[0]


@router.post("/{income_id}/reverse", response_model=IncomeResponse)
def reverse_income(
    income_id: int,
    reversal: IncomeReverse,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # Lock the row, so two people can't reverse it at the same moment
    income = db.get(Income, income_id, with_for_update=True)

    if income is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Income not found"
        )

    if current_exec.role != "admin" and income.recorded_by_exec_id != current_exec.exec_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reverse income you recorded"
        )

    if income.status == "reversed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This income has already been reversed"
        )

    income.status = "reversed"

    record_audit(
        db, current_exec, "REVERSE", "incomes", income.income_id,
        old_values={"status": "active"},
        new_values={"status": "reversed", "reason": reversal.reason.strip()}
    )

    db.commit()

    return describe_income(db, [income])[0]