"""Authentication/authorization dependencies for farmer endpoints."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models import Farmer
from app.services.farmer_service import get_farmer_by_id

_bearer = HTTPBearer(auto_error=False)


def _farmer_from_credentials(
    credentials: HTTPAuthorizationCredentials | None, db: Session
) -> Farmer:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    payload = decode_access_token(credentials.credentials)
    try:
        farmer_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid access token") from exc
    farmer = get_farmer_by_id(db, farmer_id)
    if farmer is None:
        raise UnauthorizedError("Farmer account not found")
    return farmer


def get_current_farmer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Farmer:
    """Require a valid bearer token that belongs to a registered farmer."""
    return _farmer_from_credentials(credentials, db)


def get_optional_current_farmer(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Farmer | None:
    """Like get_current_farmer but returns None when no token is supplied.

    Used by read endpoints that must stay backward compatible with the public
    Phase 4 API while enforcing ownership whenever a caller authenticates.
    An invalid/expired token is always rejected (401).
    """
    if credentials is None:
        return None
    return _farmer_from_credentials(credentials, db)
