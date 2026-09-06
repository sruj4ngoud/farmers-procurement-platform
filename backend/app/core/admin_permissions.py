"""Authentication/authorization dependencies for admin endpoints."""

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.admin_security import decode_admin_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.database.connection import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Require a valid bearer token that belongs to an active district admin.

    Raises:
        UnauthorizedError: missing or invalid token.
        ForbiddenError: user is not an admin or is inactive.
    """
    if credentials is None:
        raise UnauthorizedError("Not authenticated")

    payload = decode_admin_token(credentials.credentials)

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Invalid access token") from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Admin account not found")

    if not user.is_active:
        raise ForbiddenError("Admin account is inactive")

    if user.role != "DISTRICT_ADMIN":
        raise ForbiddenError("Admin access required")

    return user
