from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from dependencies import get_current_exec, get_db, require_admin
from schemas import ExecResponse, LoginRequest, PasswordSetupLinkRequest, PasswordSetupLinkResponse, SignupRequest
from models import Exec, ExecSession, PasswordSetupToken
from security import (
    COOKIE_SECURE,
    DUMMY_PASSWORD_HASH,
    REMEMBER_ME_LENGTH,
    SESSION_COOKIE_NAME,
    SESSION_LENGTH,
    generate_session_token,
    hash_session_token,
    verify_password,
    FRONTEND_URL,
    SETUP_LINK_LENGTH,
    hash_password
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    new_exec = Exec(
        name=signup_data.name.strip(),
        email=signup_data.email.strip().lower(),
        password_hash=hash_password(signup_data.password),
        role="exec",
        is_active=True
    )

    db.add(new_exec)

    # The email column is unique, so the database rejects a duplicate sign-up
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    return {
        "message": "Sign-up received. An admin must approve your account before you can log in."
    }


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

    # Correct password, but no admin has approved this account yet
    if exec_user.approved_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is awaiting admin approval"
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


@router.post(
    "/password-setup-links",
    response_model=PasswordSetupLinkResponse
)
def create_password_setup_link(
    link_request: PasswordSetupLinkRequest,
    current_admin: Exec = Depends(require_admin),
    db: Session = Depends(get_db)
):
    target_exec = db.get(Exec, link_request.exec_id)

    if target_exec is None or not target_exec.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exec not found or inactive"
        )

    now = datetime.now(timezone.utc)

    # Expire any earlier unused links for this Exec, so only the newest one works
    db.execute(
        update(PasswordSetupToken)
        .where(
            PasswordSetupToken.exec_id == target_exec.exec_id,
            PasswordSetupToken.used_at.is_(None),
            PasswordSetupToken.expires_at > now
        )
        .values(expires_at=now)
    )

    token = generate_session_token()
    expires_at = now + SETUP_LINK_LENGTH

    db.add(
        PasswordSetupToken(
            exec_id=target_exec.exec_id,
            token_hash=hash_session_token(token),
            created_by_exec_id=current_admin.exec_id,
            expires_at=expires_at
        )
    )
    db.commit()

    return {
        "exec_name": target_exec.name,
        "setup_link": f"{FRONTEND_URL}/set-password#token={token}",
        "expires_at": expires_at
    }