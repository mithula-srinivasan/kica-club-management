from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Exec
from schemas import LoginRequest
from security import verify_password


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    # Find the Exec using their email address
    statement = select(Exec).where(
        Exec.email == credentials.email.strip().lower()
    )

    exec_user = db.scalar(statement)

    # Reject unknown, inactive, or passwordless accounts
    if (
        exec_user is None
        or not exec_user.is_active
        or exec_user.password_hash is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check the entered password against the stored hash
    if not verify_password(
        credentials.password,
        exec_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {
        "message": "Credentials verified"
    }