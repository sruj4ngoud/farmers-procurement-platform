"""Admin authentication service: username/password login and JWT issuance."""

from datetime import timedelta

from app.config.settings import settings
from app.core.admin_security import create_admin_access_token, verify_password
from app.core.exceptions import UnauthorizedError
from app.models import User


def authenticate_admin(db, username: str, password: str) -> tuple[User, str, int]:
    """Authenticate an admin user with username + password.

    Returns (user, access_token, expires_in_seconds).

    Raises:
        UnauthorizedError: invalid credentials or inactive account.
    """
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise UnauthorizedError("Invalid username or password")

    if user.role != "DISTRICT_ADMIN":
        raise UnauthorizedError("Invalid username or password")

    if not user.is_active:
        raise UnauthorizedError("Admin account is inactive")

    if not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid username or password")

    expires_in_seconds = settings.access_token_expire_minutes * 60
    token = create_admin_access_token(
        user.user_id,
        user.username,
        user.district or "",
        expires_delta=timedelta(seconds=expires_in_seconds),
    )

    return user, token, expires_in_seconds
