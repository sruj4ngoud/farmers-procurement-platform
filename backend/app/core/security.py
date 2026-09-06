"""Security helpers: JWT creation and validation.

The signing secret always comes from environment configuration (settings). No
secret is ever hard-coded in this file.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.config.settings import settings
from app.core.constants import JWT_ACCESS_TYPE, ROLE_FARMER
from app.core.exceptions import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    farmer_id: UUID,
    passbook_number: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT for a farmer.

    Args:
        farmer_id: Farmer primary key that becomes the token subject.
        passbook_number: Farmer passbook used as a convenience claim.
        expires_delta: Optional custom lifetime (used by tests to mint tokens
            that are already expired or short lived).

    Returns:
        The encoded JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = _now()
    payload: dict[str, Any] = {
        "sub": str(farmer_id),
        "passbook_number": passbook_number,
        "role": ROLE_FARMER,
        "type": JWT_ACCESS_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate and decode a JWT.

    Raises:
        UnauthorizedError: token is malformed, expired, or not an access token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:  # pragma: no cover - trivially raised
        raise UnauthorizedError("Access token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid access token") from exc

    if payload.get("type") != JWT_ACCESS_TYPE:
        raise UnauthorizedError("Invalid access token")
    return payload
