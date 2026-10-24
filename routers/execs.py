from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dependencies import get_db, require_admin
from models import Exec
from schemas import ExecResponse


router = APIRouter(
    prefix="/execs",
    tags=["Exec management"],
    dependencies=[Depends(require_admin)]
)


def get_exec_or_404(db: Session, exec_id: int) -> Exec:
    exec_user = db.get(Exec, exec_id)

    if exec_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exec not found"
        )

    return exec_user


@router.get("/pending", response_model=list[ExecResponse])
def get_pending_signups(db: Session = Depends(get_db)):
    statement = (
        select(Exec)
        .where(Exec.approved_at.is_(None))
        .order_by(Exec.exec_id)
    )

    return db.scalars(statement).all()


@router.post("/{exec_id}/approve", response_model=ExecResponse)
def approve_signup(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    if exec_user.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account is already approved"
        )

    exec_user.approved_at = datetime.now(timezone.utc)
    exec_user.approved_by_exec_id = current_admin.exec_id
    db.commit()

    return exec_user


@router.delete("/{exec_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_signup(
    exec_id: int,
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    # Approved Execs may have history attached, so they are deactivated, never deleted
    if exec_user.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending sign-ups can be rejected"
        )

    db.delete(exec_user)
    db.commit()