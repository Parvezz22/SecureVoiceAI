import os
import secrets
import hmac

from dotenv import load_dotenv
from pwdlib import PasswordHash
from fastapi import Request, HTTPException, status

from database import get_admin_user


# Load environment variables
load_dotenv()

# Session configuration
SESSION_SECRET = os.getenv("SESSION_SECRET")

if not SESSION_SECRET or len(SESSION_SECRET) < 64:
    raise RuntimeError(
        "SESSION_SECRET is missing or invalid. Check your .env file."
    )

SESSION_MAX_AGE = 3600  # 1 hour


# Password hashing
password_hasher = PasswordHash.recommended()


def hash_password(password):
    return password_hasher.hash(password)


def verify_password(password, password_hash):
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


# Admin authentication
def authenticate_admin(username, password):
    admin = get_admin_user(username)

    if not admin:
        return None

    if not admin["is_active"]:
        return None

    if not verify_password(password, admin["password_hash"]):
        return None

    return {
        "id": admin["id"],
        "username": admin["username"]
    }


# Session validation
def get_session_admin(request: Request):
    username = request.session.get("admin_username")

    if not username:
        return None

    admin = get_admin_user(username)

    if not admin or not admin["is_active"]:
        request.session.clear()
        return None

    return {
        "id": admin["id"],
        "username": admin["username"]
    }


def require_admin(request: Request):
    admin = get_session_admin(request)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required."
        )

    return admin


# CSRF protection
def generate_csrf_token(request: Request):
    token = request.session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token

    return token


def validate_csrf_token(request: Request, submitted_token):
    stored_token = request.session.get("csrf_token")

    if (
        not stored_token
        or not submitted_token
        or not hmac.compare_digest(stored_token, submitted_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token."
        )

    return True