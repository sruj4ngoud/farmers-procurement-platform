"""Admin request/response schemas for auth, dashboard, and master data CRUD."""

from datetime import date
from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────────────


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: str
    username: str
    district: str
    admin_name: str
    expires_in_seconds: int


# ── Dashboard ─────────────────────────────────────────────────────────────────


class AdminDashboardResponse(BaseModel):
    district: str
    total_farmers: int
    active_bookings: int
    pending_reviews: int
    today_bookings: int
    farmers_in_queue: int
    active_centres: int
    today_procurement: int
    payments_processing: int
    total_centres: int
    total_slots: int
    total_bookings: int


class MandalOverviewItem(BaseModel):
    mandal_id: str
    mandal_name: str
    farmers: int
    bookings: int
    active_queue: int
    procurement_completed: int
    payments_pending: int


class MandalDetailResponse(BaseModel):
    mandal_id: str
    mandal_name: str
    district: str
    farmers: int
    centres: int
    bookings: int
    active_queue: int
    procurement_completed: int
    payments_pending: int
    recent_bookings: list[dict]


# ── Crop CRUD ─────────────────────────────────────────────────────────────────


class CropCreate(BaseModel):
    crop_name: str = Field(min_length=1, max_length=120)
    crop_category: str = Field(min_length=1, max_length=60)
    msp_per_quintal: float | None = None
    msp_effective_date: date | None = None


class CropUpdate(BaseModel):
    crop_name: str | None = None
    crop_category: str | None = None
    msp_per_quintal: float | None = None
    msp_effective_date: date | None = None
    is_active: bool | None = None


class CropResponse(BaseModel):
    crop_id: str
    crop_name: str
    crop_category: str
    is_active: bool
    msp_per_quintal: float | None
    msp_effective_date: str | None


# ── Centre CRUD ───────────────────────────────────────────────────────────────


class CentreCreate(BaseModel):
    centre_code: str = Field(min_length=1, max_length=32)
    centre_name: str = Field(min_length=1, max_length=160)
    agency: str = Field(min_length=1, max_length=64)
    village: str = Field(min_length=1, max_length=120)
    mandal: str = Field(min_length=1, max_length=120)
    latitude: float | None = None
    longitude: float | None = None
    capacity: int = Field(gt=0)
    current_status: str = "ACTIVE"


class CentreUpdate(BaseModel):
    centre_name: str | None = None
    agency: str | None = None
    village: str | None = None
    mandal: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None
    current_status: str | None = None


class CentreAdminResponse(BaseModel):
    centre_id: str
    centre_code: str
    centre_name: str
    agency: str
    village: str
    mandal: str
    district: str
    latitude: float | None
    longitude: float | None
    capacity: int
    current_status: str


# ── Slot CRUD ─────────────────────────────────────────────────────────────────


class SlotCreate(BaseModel):
    centre_id: str
    slot_date: date
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    maximum_farmers: int = Field(gt=0)
    is_active: bool = True


class SlotUpdate(BaseModel):
    slot_date: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    maximum_farmers: int | None = None
    is_active: bool | None = None


class SlotAdminResponse(BaseModel):
    slot_id: str
    centre_id: str
    centre_name: str | None = None
    slot_date: str
    start_time: str
    end_time: str
    maximum_farmers: int
    booked_farmers: int
    is_active: bool
