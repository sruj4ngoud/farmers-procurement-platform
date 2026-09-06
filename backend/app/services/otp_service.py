"""OTP issuance and verification.

OTPs are generated in memory (keyed by the farmer's mobile number). No database
table is required for Phase 5: there is no real SMS gateway yet and a process
local store is sufficient for the demo/test flow. Production SMS integration can
replace this store without changing the request/verify contract.

Demo mode (settings.otp_demo_mode, default on) surfaces the generated code in the
request response so the complete journey can be exercised safely for testing.
"""

import random
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.constants import OTP_MAX_ATTEMPTS
from app.core.exceptions import BadRequestError, NotFoundError, UnauthorizedError
from app.models import Farmer
from app.services.farmer_service import get_farmer_by_passbook_number


@dataclass
class _OtpRecord:
    otp_code: str
    farmer_id: UUID
    expires_at: datetime
    attempts: int = 0


_otp_store: dict[str, _OtpRecord] = {}
_store_lock = threading.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def request_otp(
    db: Session, passbook_number: str, mobile_number: str
) -> dict:
    """Validate the farmer's passbook + mobile and issue an OTP.

    Returns a dict with the expiry and (in demo mode) the generated OTP.
    """
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if farmer is None:
        raise NotFoundError("Farmer not found")

    if farmer.mobile_number != mobile_number:
        raise BadRequestError("Mobile number does not match the farmer passbook")

    otp_length = settings.otp_length
    otp_code = "".join(
        str(random.SystemRandom().randint(0, 9)) for _ in range(otp_length)
    )

    expiry = timedelta(seconds=settings.otp_expiry_seconds)
    record = _OtpRecord(
        otp_code=otp_code,
        farmer_id=farmer.farmer_id,
        expires_at=_utcnow() + expiry,
    )
    with _store_lock:
        _otp_store[farmer.mobile_number] = record

    result = {
        "expires_in_seconds": settings.otp_expiry_seconds,
        "demo_otp": otp_code if settings.otp_demo_mode else None,
    }
    return result


def verify_otp(
    db: Session, passbook_number: str, mobile_number: str, otp_code: str
) -> Farmer:
    """Verify an OTP and return the owning farmer on success.

    Raises:
        NotFoundError: farmer does not exist.
        BadRequestError: mobile mismatch.
        UnauthorizedError: OTP missing, wrong, expired, or too many attempts.
    """
    farmer = get_farmer_by_passbook_number(db, passbook_number)
    if farmer is None:
        raise NotFoundError("Farmer not found")
    if farmer.mobile_number != mobile_number:
        raise BadRequestError("Mobile number does not match the farmer passbook")

    with _store_lock:
        record = _otp_store.get(farmer.mobile_number)

    if record is None:
        raise UnauthorizedError("No OTP requested for this number. Request a new OTP.")

    if record.farmer_id != farmer.farmer_id:
        raise UnauthorizedError("Invalid OTP")

    if _utcnow() > record.expires_at:
        with _store_lock:
            _otp_store.pop(farmer.mobile_number, None)
        raise UnauthorizedError("OTP has expired. Request a new OTP.")

    if record.attempts >= OTP_MAX_ATTEMPTS:
        with _store_lock:
            _otp_store.pop(farmer.mobile_number, None)
        raise UnauthorizedError("Too many failed attempts. Request a new OTP.")

    if otp_code != record.otp_code:
        record.attempts += 1
        raise UnauthorizedError("Invalid OTP")

    with _store_lock:
        _otp_store.pop(farmer.mobile_number, None)
    return farmer


def clear_otp_store() -> None:
    """Clear all issued OTPs (mainly useful between tests)."""
    with _store_lock:
        _otp_store.clear()
