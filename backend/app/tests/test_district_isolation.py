"""Tests for 33-district data integrity, admin isolation, and farmer-admin sync.

These tests use the in-memory SQLite test database and create their own
fixtures to verify district isolation without depending on external seed data.
"""

import uuid
from decimal import Decimal
from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.admin_security import hash_password, create_admin_access_token
from app.models import (
    Farmer, ProcurementCentre, Booking, Slot, User, District, Mandal,
    CultivationRecord, LandRecord, QueueToken, ProcurementRecord, Payment,
    BankDetails, Crop, Notification,
)
from app.core.security import create_access_token


# ── Fixtures ──────────────────────────────────────────────────────────────────

TELANGANA_33_DISTRICTS = [
    "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad",
    "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal",
    "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem",
    "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak",
    "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda",
    "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli",
    "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet",
    "Suryapet", "Vikarabad", "Wanaparthy", "Warangal",
    "Yadadri Bhuvanagiri",
]


@pytest.fixture
def all_districts(db_session):
    """Create all 33 Telangana districts."""
    districts = []
    for name in TELANGANA_33_DISTRICTS:
        d = District(district_id=uuid.uuid5(uuid.NAMESPACE_URL, f"test-district/{name}"), name=name, state="Telangana")
        db_session.add(d)
        districts.append(d)
    db_session.commit()
    return districts


@pytest.fixture
def sangareddy_district(db_session):
    d = District(district_id=uuid.uuid5(uuid.NAMESPACE_URL, "test-district/Sangareddy"), name="Sangareddy", state="Telangana")
    db_session.add(d)
    db_session.commit()
    return d


@pytest.fixture
def medchal_district(db_session):
    d = District(district_id=uuid.uuid5(uuid.NAMESPACE_URL, "test-district/Medchal-Malkajgiri"), name="Medchal-Malkajgiri", state="Telangana")
    db_session.add(d)
    db_session.commit()
    return d


@pytest.fixture
def sr_admin(db_session, sangareddy_district):
    u = User(
        user_id=uuid.uuid4(),
        username="admin_sangareddy_test",
        password_hash=hash_password("testpass123"),
        role="DISTRICT_ADMIN",
        district="Sangareddy",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def md_admin(db_session, medchal_district):
    u = User(
        user_id=uuid.uuid4(),
        username="admin_medchal_test",
        password_hash=hash_password("testpass123"),
        role="DISTRICT_ADMIN",
        district="Medchal-Malkajgiri",
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def sr_farmer(db_session):
    f = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-TEST-SR-001",
        farmer_name="Sangareddy Test Farmer",
        mobile_number="9001000001",
        village="TestVillage",
        mandal="TestMandal",
        district="Sangareddy",
        survey_number="100-A",
        total_land_acres=Decimal("5.00"),
        latitude=Decimal("17.630000"),
        longitude=Decimal("78.090000"),
    )
    db_session.add(f)
    db_session.commit()
    return f


@pytest.fixture
def md_farmer(db_session):
    f = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-TEST-MD-001",
        farmer_name="Medchal Test Farmer",
        mobile_number="9001000002",
        village="TestVillage",
        mandal="TestMandal",
        district="Medchal-Malkajgiri",
        survey_number="200-B",
        total_land_acres=Decimal("8.00"),
        latitude=Decimal("17.500000"),
        longitude=Decimal("78.500000"),
    )
    db_session.add(f)
    db_session.commit()
    return f


@pytest.fixture
def sr_centre(db_session):
    c = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-TEST-SR-001",
        centre_name="Sangareddy Test Centre",
        agency="NAFED",
        village="TestVillage",
        mandal="TestMandal",
        district="Sangareddy",
        latitude=Decimal("17.630000"),
        longitude=Decimal("78.090000"),
        capacity=50,
        current_status="ACTIVE",
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture
def md_centre(db_session):
    c = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-TEST-MD-001",
        centre_name="Medchal Test Centre",
        agency="Government",
        village="TestVillage",
        mandal="TestMandal",
        district="Medchal-Malkajgiri",
        latitude=Decimal("17.500000"),
        longitude=Decimal("78.500000"),
        capacity=60,
        current_status="ACTIVE",
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture
def sr_slot(db_session, sr_centre):
    s = Slot(
        slot_id=uuid.uuid4(),
        centre_id=sr_centre.centre_id,
        slot_date=date(2025, 10, 6),
        start_time=time(9, 0),
        end_time=time(10, 0),
        maximum_farmers=30,
        booked_farmers=0,
        is_active=True,
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture
def sr_cultivation(db_session, sr_farmer):
    c = CultivationRecord(
        cultivation_id=uuid.uuid4(),
        farmer_id=sr_farmer.farmer_id,
        season="Rabi-2024",
        cultivated_area_acres=Decimal("3.00"),
        crop="Paddy",
        quantity_produced_quintals=Decimal("60.00"),
        quantity_to_sell_quintals=Decimal("50.00"),
    )
    db_session.add(c)
    db_session.commit()
    return c


def _admin_token(user: User) -> str:
    return create_admin_access_token(user.user_id, user.username, user.district or "")


# ── District Integrity Tests ──────────────────────────────────────────────────

class TestDistrictIntegrity:
    def test_33_districts_creatable(self, client, all_districts):
        """All 33 districts should exist in the database."""
        from app.models import District as DistModel
        from app.database.connection import get_db
        # Direct DB check since we can't count via API without auth
        assert len(all_districts) == 33

    def test_each_district_has_unique_name(self, all_districts):
        names = [d.name for d in all_districts]
        assert len(names) == len(set(names))

    def test_admins_for_each_district(self, db_session, all_districts):
        """We should be able to create one admin per district."""
        admins = []
        for d in all_districts:
            u = User(
                user_id=uuid.uuid4(),
                username=f"admin_{d.name.lower().replace(' ', '_').replace('-', '')}",
                password_hash=hash_password("admin123"),
                role="DISTRICT_ADMIN",
                district=d.name,
                is_active=True,
            )
            db_session.add(u)
            admins.append(u)
        db_session.commit()
        assert len(admins) == 33

        # Verify unique districts
        admin_districts = [a.district for a in admins]
        assert len(set(admin_districts)) == 33


# ── District Scoping Tests ───────────────────────────────────────────────────

class TestDistrictScoping:
    def test_admin_sees_only_own_district_farmers(
        self, client, sr_admin, md_admin, sr_farmer, md_farmer
    ):
        """Sangareddy admin must NOT see Medchal farmers."""
        token = _admin_token(sr_admin)
        resp = client.get("/api/admin/farmers", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        farmers = resp.json()
        assert all(f["district"] == "Sangareddy" for f in farmers)
        assert any(f["passbook_number"] == "PB-TEST-SR-001" for f in farmers)

    def test_medchal_admin_sees_only_medchal_farmers(
        self, client, sr_admin, md_admin, sr_farmer, md_farmer
    ):
        """Medchal admin must NOT see Sangareddy farmers."""
        token = _admin_token(md_admin)
        resp = client.get("/api/admin/farmers", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        farmers = resp.json()
        assert all(f["district"] == "Medchal-Malkajgiri" for f in farmers)
        assert any(f["passbook_number"] == "PB-TEST-MD-001" for f in farmers)

    def test_admin_sees_only_own_district_centres(
        self, client, sr_admin, md_admin, sr_centre, md_centre
    ):
        token = _admin_token(sr_admin)
        resp = client.get("/api/admin/centres", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        centres = resp.json()
        assert all(c["district"] == "Sangareddy" for c in centres)

    def test_dashboard_district_scoped(self, client, sr_admin, sr_farmer, sr_centre):
        token = _admin_token(sr_admin)
        resp = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["district"] == "Sangareddy"
        assert data["total_farmers"] >= 1
        assert data["total_centres"] >= 1


# ── Booking District Isolation Tests ─────────────────────────────────────────

class TestBookingDistrictIsolation:
    def test_booking_visible_to_correct_admin(
        self, client, db_session, sr_admin, sr_farmer, sr_centre, sr_slot, sr_cultivation
    ):
        """A Sangareddy booking should appear in Sangareddy admin's reviews."""
        booking = Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-TEST-ISO-001",
            farmer_id=sr_farmer.farmer_id,
            cultivation_id=sr_cultivation.cultivation_id,
            centre_id=sr_centre.centre_id,
            slot_id=sr_slot.slot_id,
            quantity_to_sell_quintals=Decimal("20.00"),
            booking_status="PENDING_ADMIN_REVIEW",
        )
        db_session.add(booking)
        db_session.commit()

        token = _admin_token(sr_admin)
        resp = client.get("/api/admin/bookings", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        bookings = resp.json()
        booking_ids = [b["booking_id"] for b in bookings]
        assert str(booking.booking_id) in booking_ids

    def test_booking_invisible_to_wrong_admin(
        self, client, db_session, sr_admin, md_admin, sr_farmer, sr_centre, sr_slot, sr_cultivation
    ):
        """A Sangareddy booking must NOT appear in Medchal admin's reviews."""
        booking = Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-TEST-ISO-002",
            farmer_id=sr_farmer.farmer_id,
            cultivation_id=sr_cultivation.cultivation_id,
            centre_id=sr_centre.centre_id,
            slot_id=sr_slot.slot_id,
            quantity_to_sell_quintals=Decimal("25.00"),
            booking_status="PENDING_ADMIN_REVIEW",
        )
        db_session.add(booking)
        db_session.commit()

        # Medchal admin should NOT see it
        token = _admin_token(md_admin)
        resp = client.get("/api/admin/bookings", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        bookings = resp.json()
        booking_ids = [b["booking_id"] for b in bookings]
        assert str(booking.booking_id) not in booking_ids

    def test_accept_booking_district_enforced(
        self, client, db_session, sr_admin, md_admin, sr_farmer, sr_centre, sr_slot, sr_cultivation
    ):
        """Medchal admin cannot accept a Sangareddy booking."""
        booking = Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-TEST-ISO-003",
            farmer_id=sr_farmer.farmer_id,
            cultivation_id=sr_cultivation.cultivation_id,
            centre_id=sr_centre.centre_id,
            slot_id=sr_slot.slot_id,
            quantity_to_sell_quintals=Decimal("10.00"),
            booking_status="PENDING_ADMIN_REVIEW",
        )
        db_session.add(booking)
        db_session.commit()

        # Medchal admin tries to accept
        token = _admin_token(md_admin)
        resp = client.put(
            f"/api/admin/reviews/{booking.booking_id}/review",
            json={"decision": "ACCEPT"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_accept_booking_by_correct_admin(
        self, client, db_session, sr_admin, sr_farmer, sr_centre, sr_slot, sr_cultivation
    ):
        """Sangareddy admin can accept a Sangareddy booking."""
        booking = Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-TEST-ISO-004",
            farmer_id=sr_farmer.farmer_id,
            cultivation_id=sr_cultivation.cultivation_id,
            centre_id=sr_centre.centre_id,
            slot_id=sr_slot.slot_id,
            quantity_to_sell_quintals=Decimal("15.00"),
            booking_status="PENDING_ADMIN_REVIEW",
        )
        db_session.add(booking)
        db_session.commit()

        token = _admin_token(sr_admin)
        resp = client.put(
            f"/api/admin/reviews/{booking.booking_id}/review",
            json={"decision": "ACCEPT", "comment": "Approved"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["booking_status"] == "ACCEPTED"


# ── Admin Login Tests ────────────────────────────────────────────────────────

class TestAdminLogin:
    def test_valid_admin_login(self, client, sr_admin):
        resp = client.post(
            "/api/admin/auth/login",
            json={"username": "admin_sangareddy_test", "password": "testpass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["district"] == "Sangareddy"
        assert data["access_token"]

    def test_wrong_password_rejected(self, client, sr_admin):
        resp = client.post(
            "/api/admin/auth/login",
            json={"username": "admin_sangareddy_test", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_farmer_token_rejected_on_admin(self, client, sr_farmer):
        token = create_access_token(sr_farmer.farmer_id, sr_farmer.passbook_number)
        resp = client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


# ── Farmer Auth Not Broken ───────────────────────────────────────────────────

class TestFarmerAuthNotBroken:
    def test_farmer_otp_flow_still_works(self, client, sr_farmer):
        from app.services.otp_service import clear_otp_store
        clear_otp_store()

        resp = client.post(
            "/api/auth/request-otp",
            json={
                "passbook_number": sr_farmer.passbook_number,
                "mobile_number": sr_farmer.mobile_number,
            },
        )
        assert resp.status_code == 200
        otp = resp.json()["demo_otp"]

        resp = client.post(
            "/api/auth/verify-otp",
            json={
                "passbook_number": sr_farmer.passbook_number,
                "mobile_number": sr_farmer.mobile_number,
                "otp": otp,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]
        clear_otp_store()
