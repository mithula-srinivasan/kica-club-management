from club_time import kuwait_today

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from audit import record_audit
from dependencies import get_current_exec, get_db
from models import Exec, Expense
from schemas import ExpenseCreate, ExpenseResponse, ExpenseReverse



router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
    dependencies=[Depends(get_current_exec)]
)


def describe_expenses(db: Session, expenses: list[Expense]) -> list[dict]:
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    return [
        {
            "expense_id": e.expense_id,
            "description": e.description,
            "amount": e.amount,
            "expense_date": e.expense_date,
            "status": e.status,
            "recorded_by_exec_id": e.recorded_by_exec_id,
            "recorded_by_name": exec_names[e.recorded_by_exec_id],
            "created_at": e.created_at
        }
        for e in expenses
    ]


@router.get("/", response_model=list[ExpenseResponse])
def list_expenses(db: Session = Depends(get_db)):
    expenses = db.scalars(
        select(Expense).order_by(
            Expense.expense_date.desc(),
            Expense.expense_id.desc()
        )
    ).all()

    return describe_expenses(db, expenses)


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def record_expense(
    expense_data: ExpenseCreate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    if expense_data.expense_date > kuwait_today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Expense date cannot be in the future"
        )

    description = expense_data.description.strip()

    if not description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Description cannot be empty"
        )

    expense = Expense(
        description=description,
        amount=expense_data.amount,
        expense_date=expense_data.expense_date,
        # The person recording the expense paid it from the club money they hold
        paid_by_exec_id=current_exec.exec_id,
        recorded_by_exec_id=current_exec.exec_id,
        funding_source="club_funds",
        status="active"
    )
    db.add(expense)
    db.flush()

    record_audit(
        db, current_exec, "CREATE", "expenses", expense.expense_id,
        new_values={
            "description": description,
            "amount": expense.amount,
            "expense_date": expense.expense_date
        }
    )

    db.commit()

    return describe_expenses(db, [expense])[0]


@router.post("/{expense_id}/reverse", response_model=ExpenseResponse)
def reverse_expense(
    expense_id: int,
    reversal: ExpenseReverse,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    # Lock the row, so two people can't reverse it at the same moment
    expense = db.get(Expense, expense_id, with_for_update=True)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    if current_exec.role != "admin" and expense.recorded_by_exec_id != current_exec.exec_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reverse expenses you recorded"
        )

    if expense.status == "reversed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This expense has already been reversed"
        )

    expense.status = "reversed"

    record_audit(
        db, current_exec, "REVERSE", "expenses", expense.expense_id,
        old_values={"status": "active"},
        new_values={"status": "reversed", "reason": reversal.reason.strip()}
    )

    db.commit()

    return describe_expenses(db, [expense])[0]