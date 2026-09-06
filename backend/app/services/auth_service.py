"""Authentication service: OTP-based farmer login and JWT issuance."""

from datetime import timedelta

from app.config.settings import settings
from app.core.security import create_access_token
from app.models import Farmer


def issue_farmer_token(farmer: Farmer) -> tuple[str, int]:
    """Issue a JWT for a verified farmer.

    Returns (access_token, expires_in_seconds).
    """
    expires_in_seconds = settings.access_token_expire_minutes * 60
    token = create_access_token(
        farmer.farmer_id,
        farmer.passbook_number,
        expires_delta=timedelta(seconds=expires_in_seconds),
    )
    return token, expires_in_seconds
