"""Booking number generation helpers."""

import uuid
from datetime import datetime, timezone


def generate_booking_number() -> str:
    """Generate a human-friendly, effectively unique booking number."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"BK-{date_part}-{suffix}"
