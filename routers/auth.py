from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dependencies import get_current_exec, get_db
from schemas import ExecResponse, LoginRequest
from models import Exec, ExecSession
from schemas import LoginRequest
from security import (
    COOKIE_SECURE,
    DUMMY_PASSWORD_HASH,
    REMEMBER_ME_LENGTH,
    SESSION_COOKIE_NAME,
    SESSION_LENGTH,
    generate_session_token,
    hash_session_token,
    verify_password,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/login")
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    # Find the Exec using their email address
    statement = select(Exec).where(
        Exec.email == credentials.email.strip().lower()
    )

    exec_user = db.scalar(statement)

    # Always run one password check, so every failed login takes the same time
    if exec_user is None or exec_user.password_hash is None:
        verify_password(credentials.password, DUMMY_PASSWORD_HASH)
        password_ok = False
    else:
        password_ok = verify_password(
            credentials.password,
            exec_user.password_hash
        )

    # Reject wrong passwords, unknown or passwordless accounts, and inactive accounts
    if not password_ok or not exec_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create a new session for this device
    token = generate_session_token()

    if credentials.remember_me:
        lifetime = REMEMBER_ME_LENGTH
    else:
        lifetime = SESSION_LENGTH

    new_session = ExecSession(
        exec_id=exec_user.exec_id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + lifetime
    )

    db.add(new_session)
    db.commit()

    # Give the raw token to the browser as a cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(lifetime.total_seconds()) if credentials.remember_me else None,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE
    )

    return {
        "message": "Logged in",
        "name": exec_user.name,
        "role": exec_user.role
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    token = request.cookies.get(SESSION_COOKIE_NAME)

    # Delete this device's session so the cookie stops working immediately
    if token:
        db.execute(
            delete(ExecSession).where(
                ExecSession.token_hash == hash_session_token(token)
            )
        )
        db.commit()

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE
    )

    return {"message": "Logged out"}


@router.get("/me", response_model=ExecResponse)
def read_current_exec(
    current_exec: Exec = Depends(get_current_exec)
):
    return current_exec