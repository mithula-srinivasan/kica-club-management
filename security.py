import hashlib
import os
import secrets
from datetime import timedelta

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

SESSION_COOKIE_NAME = "kica_session"
SESSION_LENGTH = timedelta(hours=12)
REMEMBER_ME_LENGTH = timedelta(days=30)

# Browsers only send Secure cookies over HTTPS, so this must be "true" in production
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false") == "true"

# Used so a login for an unknown email takes as long as one for a real account
DUMMY_PASSWORD_HASH = password_hash.hash("timing-protection-dummy")


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


SETUP_LINK_LENGTH = timedelta(hours=24)

# Where the React app runs; setup links point to its "set password" page
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

RESET_LINK_LENGTH = timedelta(hours=1)

# Where the React app runs; reset links point to its "reset password" page
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")