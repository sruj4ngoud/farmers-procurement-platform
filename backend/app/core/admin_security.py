"""Admin security: password hashing and admin JWT creation/verification."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.config.settings import settings
from app.core.constants import JWT_ACCESS_TYPE
from app.core.exceptions import UnauthorizedError, ForbiddenError


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_admin_access_token(
    admin_user_id: UUID,
    username: str,
    district: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT for an admin user."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = _now()
    payload: dict[str, Any] = {
        "sub": str(admin_user_id),
        "username": username,
        "role": "DISTRICT_ADMIN",
        "district": district,
        "type": JWT_ACCESS_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_admin_token(token: str) -> dict[str, Any]:
    """Validate and decode an admin JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Access token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid access token") from exc

    if payload.get("type") != JWT_ACCESS_TYPE:
        raise UnauthorizedError("Invalid access token")

    if payload.get("role") != "DISTRICT_ADMIN":
        raise ForbiddenError("Admin access required")

    return payload
