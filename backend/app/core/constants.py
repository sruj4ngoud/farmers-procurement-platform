"""Shared application constants."""

from datetime import timedelta

# Roles used by the platform's user accounts. Farmers authenticate through
# passbook + mobile + OTP and are represented by the Farmer record itself.
ROLE_FARMER = "FARMER"
ROLE_CENTRE_STAFF = "CENTRE_STAFF"
ROLE_ADMIN = "ADMIN"

# JWT configuration defaults.
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TYPE = "access"

# OTP defaults (overridable via settings / environment).
OTP_DEFAULT_LENGTH = 6
OTP_DEFAULT_EXPIRY = timedelta(minutes=5)
OTP_MAX_ATTEMPTS = 5

# Booking statuses that represent an active, committed sale (consume capacity).
# These statuses all count against slot capacity.
CONFIRMED_BOOKING_STATUSES = (
    "PENDING_ADMIN_REVIEW",
    "ACCEPTED",
    "AUTO_ACCEPTED",
    "CONFIRMED",  # legacy
)

# Booking statuses that indicate admin has acted.
ADMIN_REVIEWED_STATUSES = ("ACCEPTED", "REJECTED", "AUTO_ACCEPTED")

# Booking statuses visible to the farmer as "active".
FARMER_ACTIVE_STATUSES = (
    "PENDING_ADMIN_REVIEW",
    "ACCEPTED",
    "AUTO_ACCEPTED",
    "CONFIRMED",  # legacy
)

# Queue token statuses that are still "in line".
ACTIVE_QUEUE_STATUSES = ("WAITING", "CALLED", "PROCESSING")
CANCELLED_QUEUE_STATUSES = ("CANCELLED", "SKIPPED", "COMPLETED")

# Direction of money movement. Government always pays the farmer; farmers never pay.
PAYMENT_DIRECTION_GOVERNMENT_TO_FARMER = "GOVERNMENT_TO_FARMER"

# Notification types raised for the farmer workflow.
NOTIFICATION_BOOKING_CREATED = "BOOKING_CONFIRMED"
NOTIFICATION_TOKEN_GENERATED = "TOKEN_GENERATED"
NOTIFICATION_PROCUREMENT_COMPLETED = "PROCUREMENT_COMPLETED"
NOTIFICATION_PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
