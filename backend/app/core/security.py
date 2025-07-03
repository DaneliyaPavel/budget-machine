import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 14

_pwd_hasher = PasswordHasher()

PASSWORD_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$")


def validate_password(password: str) -> None:
    """Validate password complexity."""
    if not PASSWORD_RE.match(password):
        raise ValueError(
            "Password must be at least 12 characters long and include "
            "an uppercase letter, a digit and a special symbol"
        )


def get_password_hash(password: str) -> str:
    """Hash password using Argon2."""
    return _pwd_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password using Argon2."""
    try:
        return _pwd_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create access JWT."""
    return _create_token(
        {"type": "access", **data}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh JWT."""
    return _create_token(
        {"type": "refresh", **data}, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str) -> Dict[str, Any]:
    """Decode JWT without validation."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
