from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from email_service import send_email
from dependencies import get_current_exec, get_db, require_admin
from schemas import ExecResponse, LoginRequest, PasswordSetupLinkRequest, PasswordSetupLinkResponse, SignupRequest, ForgotPasswordRequest, ResetPasswordRequest
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
    hash_password,
    RESET_LINK_LENGTH
)

from rate_limit import (
    LOGIN_LIMIT_PER_EMAIL,
    LOGIN_LIMIT_PER_IP,
    LOGIN_MESSAGE,
    LOGIN_WINDOW,
    RESET_LIMIT_PER_EMAIL,
    RESET_LIMIT_PER_IP,
    RESET_MESSAGE,
    RESET_WINDOW,
    SIGNUP_LIMIT_PER_IP,
    SIGNUP_MESSAGE,
    SIGNUP_WINDOW,
    check_rate_limit,
    clear_hits,
    client_ip,
    record_hit,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    signup_data: SignupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    # At most a few sign-ups per hour from the same network
    ip_key = f"signup-ip:{client_ip(request)}"
    check_rate_limit(db, ip_key, SIGNUP_LIMIT_PER_IP, SIGNUP_WINDOW, SIGNUP_MESSAGE)
    record_hit(db, ip_key)
    db.commit()

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
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    email = credentials.email.strip().lower()
    email_key = f"login-email:{email}"
    ip_key = f"login-ip:{client_ip(request)}"

    # Too many wrong passwords recently? Refuse before checking this one,
    # even if it is correct - otherwise someone could keep guessing.
    check_rate_limit(db, email_key, LOGIN_LIMIT_PER_EMAIL, LOGIN_WINDOW, LOGIN_MESSAGE)
    check_rate_limit(db, ip_key, LOGIN_LIMIT_PER_IP, LOGIN_WINDOW, LOGIN_MESSAGE)

    # Find the Exec using their email address
    exec_user = db.scalar(select(Exec).where(Exec.email == email))

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
        # Count this failed attempt for the email and for the IP
        record_hit(db, email_key)
        record_hit(db, ip_key)
        db.commit()

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

    # Logged in successfully: forget this email's earlier wrong attempts
    clear_hits(db, email_key)

    # Tidy up: remove everyone's expired sessions, which can never be used again
    db.execute(
        delete(ExecSession).where(
            ExecSession.expires_at < datetime.now(timezone.utc)
        )
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


@router.post("/forgot-password")
def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Same reply whether or not the account exists, so emails can't be checked
    generic_reply = {
        "message": "If an account exists for this email, a reset link has been sent."
    }

    email = request_data.email.strip().lower()

    # Limit reset emails per email address and per network.
    # Every request counts, whether or not the account exists.
    email_key = f"reset-email:{email}"
    ip_key = f"reset-ip:{client_ip(request)}"
    check_rate_limit(db, email_key, RESET_LIMIT_PER_EMAIL, RESET_WINDOW, RESET_MESSAGE)
    check_rate_limit(db, ip_key, RESET_LIMIT_PER_IP, RESET_WINDOW, RESET_MESSAGE)
    record_hit(db, email_key)
    record_hit(db, ip_key)
    db.commit()

    exec_user = db.scalar(
        select(Exec).where(Exec.email == email)
    )

    exec_user = db.scalar(
        select(Exec).where(Exec.email == request_data.email.strip().lower())
    )

    if (
        exec_user is None
        or not exec_user.is_active
        or exec_user.approved_at is None
    ):
        return generic_reply

    now = datetime.now(timezone.utc)

    # Tidy up: remove reset links that expired more than 30 days ago
    db.execute(
        delete(PasswordSetupToken).where(
            PasswordSetupToken.expires_at < now - timedelta(days=30)
        )
    )

    # Expire any earlier unused links, so only the newest one works
    db.execute(
        update(PasswordSetupToken)
        .where(
            PasswordSetupToken.exec_id == exec_user.exec_id,
            PasswordSetupToken.used_at.is_(None),
            PasswordSetupToken.expires_at > now
        )
        .values(expires_at=now)
    )

    token = generate_session_token()

    db.add(
        PasswordSetupToken(
            exec_id=exec_user.exec_id,
            token_hash=hash_session_token(token),
            created_by_exec_id=exec_user.exec_id,
            expires_at=now + RESET_LINK_LENGTH
        )
    )
    db.commit()

    reset_link = f"{FRONTEND_URL}/reset-password#token={token}"

    # Send after the reply, so the response time doesn't reveal that the account exists
    background_tasks.add_task(
        send_email,
        exec_user.email,
        "Reset your KICA password",
        f"Hi {exec_user.name},\n\n"
        f"Use this link to choose a new password:\n{reset_link}\n\n"
        "This link expires in 1 hour. If you didn't ask for this, you can ignore this email."
    )

    return generic_reply


@router.post("/reset-password")
def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    invalid_link = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This reset link is invalid or has expired"
    )

    now = datetime.now(timezone.utc)

    # A valid link matches, hasn't been used, and hasn't expired
    reset_token = db.scalar(
        select(PasswordSetupToken)
        .where(
            PasswordSetupToken.token_hash == hash_session_token(reset_data.token),
            PasswordSetupToken.used_at.is_(None),
            PasswordSetupToken.expires_at > now
        )
        .with_for_update()
    )

    if reset_token is None:
        raise invalid_link

    exec_user = db.get(Exec, reset_token.exec_id)

    if not exec_user.is_active:
        raise invalid_link

    exec_user.password_hash = hash_password(reset_data.new_password)
    reset_token.used_at = now

    # Log out every device, in case someone else had access to the account
    db.execute(
        delete(ExecSession).where(ExecSession.exec_id == exec_user.exec_id)
    )


    # A new password ends any login block, so the owner can log in straight away
    clear_hits(db, f"login-email:{exec_user.email}")
    
    db.commit()

    return {
        "message": "Password reset. You can now log in with your new password."
    }