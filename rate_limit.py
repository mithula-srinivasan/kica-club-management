from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from models import RateLimitHit


# ---- The limits (change the numbers here if needed) ----

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_LIMIT_PER_EMAIL = 5
LOGIN_LIMIT_PER_IP = 20
LOGIN_MESSAGE = "Too many attempts. Please try again in 15 minutes."

RESET_WINDOW = timedelta(hours=1)
RESET_LIMIT_PER_EMAIL = 3
RESET_LIMIT_PER_IP = 10
RESET_MESSAGE = "Too many reset requests. Please try again in an hour."

REGISTRATION_WINDOW = timedelta(hours=1)
REGISTRATION_LIMIT_PER_IP = 5
REGISTRATION_MESSAGE = "Too many registrations from this network. Please try again in an hour."

SIGNUP_WINDOW = timedelta(hours=1)
SIGNUP_LIMIT_PER_IP = 5
SIGNUP_MESSAGE = "Too many sign-ups from this network. Please try again in an hour."

# Hits older than this are deleted, since no limit looks back that far
KEEP_HITS_FOR = timedelta(days=1)


def client_ip(request: Request) -> str:
    """The visitor's IP address."""
    return request.client.host if request.client else "unknown"


def short(key: str) -> str:
    # Someone could send a huge "email"; keep keys within the column size
    return key[:320]


def check_rate_limit(db: Session, key: str, limit: int, window: timedelta, message: str):
    """Refuse with 429 if this key already has `limit` hits within `window`."""
    since = datetime.now(timezone.utc) - window

    recent_hits = db.scalar(
        select(func.count())
        .select_from(RateLimitHit)
        .where(
            RateLimitHit.key == short(key),
            RateLimitHit.created_at > since
        )
    )

    if recent_hits >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message
        )


def record_hit(db: Session, key: str):
    """Count one attempt for this key. The caller commits."""
    db.add(RateLimitHit(key=short(key)))

    # Tidy up old hits, so the table stays small
    db.execute(
        delete(RateLimitHit).where(
            RateLimitHit.created_at < datetime.now(timezone.utc) - KEEP_HITS_FOR
        )
    )


def clear_hits(db: Session, key: str):
    """Forget all attempts for this key, e.g. after a successful login. The caller commits."""
    db.execute(delete(RateLimitHit).where(RateLimitHit.key == short(key)))