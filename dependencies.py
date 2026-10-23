from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Exec, ExecSession
from security import SESSION_COOKIE_NAME, hash_session_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_exec(
    request: Request,
    db: Session = Depends(get_db)
) -> Exec:
    not_logged_in = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not logged in"
    )

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise not_logged_in

    # Find the Exec who owns this token, but only if the session hasn't expired
    statement = (
        select(Exec)
        .join(ExecSession, ExecSession.exec_id == Exec.exec_id)
        .where(
            ExecSession.token_hash == hash_session_token(token),
            ExecSession.expires_at > datetime.now(timezone.utc)
        )
    )

    exec_user = db.scalar(statement)

    # Deactivated Execs are locked out even if their session hasn't expired
    if exec_user is None or not exec_user.is_active:
        raise not_logged_in

    return exec_user