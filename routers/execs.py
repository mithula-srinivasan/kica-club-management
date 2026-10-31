from datetime import datetime, timezone
from audit import record_audit

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from dependencies import get_db, require_admin
from models import Exec, ExecSession
from schemas import ExecResponse, ExecAdminResponse


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


@router.get("/", response_model=list[ExecAdminResponse])
def list_execs(db: Session = Depends(get_db)):
    # Approved Execs only: pending sign-ups are listed separately
    return db.scalars(
        select(Exec)
        .where(Exec.approved_at.is_not(None))
        .order_by(Exec.name)
    ).all()



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

    record_audit(
        db, current_admin, "UPDATE", "execs", exec_user.exec_id,
        old_values={"approved_at": None},
        new_values={"approved_at": exec_user.approved_at}
    )
    db.commit()

    return exec_user


@router.delete("/{exec_id}", status_code=status.HTTP_204_NO_CONTENT)
def reject_signup(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    # Approved Execs may have history attached, so they are deactivated, never deleted
    if exec_user.approved_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending sign-ups can be rejected"
        )

    record_audit(
        db, current_admin, "DELETE", "execs", exec_user.exec_id,
        old_values={"name": exec_user.name, "email": exec_user.email}
    )
    db.delete(exec_user)
    db.commit()


@router.post("/{exec_id}/make-admin", response_model=ExecResponse)
def make_admin(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    if exec_user.approved_at is None or not exec_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only approved, active Execs can be made admin"
        )

    if exec_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Exec is already an admin"
        )

    exec_user.role = "admin"

    record_audit(
        db, current_admin, "UPDATE", "execs", exec_user.exec_id,
        old_values={"role": "exec"},
        new_values={"role": "admin"}
    )
    db.commit()

    return exec_user


@router.post("/{exec_id}/remove-admin", response_model=ExecResponse)
def remove_admin(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    if exec_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Exec is not an admin"
        )

    # Never leave the club with no admin, or nobody could approve or manage accounts
    active_admin_count = db.scalar(
        select(func.count())
        .select_from(Exec)
        .where(Exec.role == "admin", Exec.is_active.is_(True))
    )

    if active_admin_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove the last admin"
        )

    exec_user.role = "exec"

    record_audit(
        db, current_admin, "UPDATE", "execs", exec_user.exec_id,
        old_values={"role": "admin"},
        new_values={"role": "exec"}
    )
    db.commit()

    return exec_user



@router.post("/{exec_id}/deactivate", response_model=ExecResponse)
def deactivate_exec(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    # Stops an admin locking themselves out, and means the last admin can never be deactivated
    if exec_user.exec_id == current_admin.exec_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot deactivate your own account"
        )

    if exec_user.approved_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pending sign-ups should be rejected, not deactivated"
        )

    if not exec_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Exec is already deactivated"
        )

    exec_user.is_active = False

    # Log them out on every device straight away
    db.execute(
        delete(ExecSession).where(ExecSession.exec_id == exec_user.exec_id)
    )

    record_audit(
        db, current_admin, "UPDATE", "execs", exec_user.exec_id,
        old_values={"is_active": True},
        new_values={"is_active": False}
    )
    db.commit()

    return exec_user


@router.post("/{exec_id}/reactivate", response_model=ExecResponse)
def reactivate_exec(
    exec_id: int,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exec_user = get_exec_or_404(db, exec_id)

    if exec_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Exec is already active"
        )

    exec_user.is_active = True

    record_audit(
        db, current_admin, "UPDATE", "execs", exec_user.exec_id,
        old_values={"is_active": False},
        new_values={"is_active": True}
    )
    db.commit()

    return exec_user