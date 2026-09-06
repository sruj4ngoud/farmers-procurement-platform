"""Phase 7.1 + 7.2 admin authentication, district-scoped authorization, and mandal tests."""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.admin_security import hash_password
from app.models import Farmer, ProcurementCentre, Booking, Slot, User, District, Mandal
from app.core.security import create_access_token


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_user(db_session) -> User:
    """Create an active district admin for Sangareddy."""
    user = User(
        user_id=uuid.uuid4(),
        username="admin_test_sangareddy",
        password_hash=hash_password("testpass123"),
        role="DISTRICT_ADMIN",
        district="Sangareddy",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user_medchal(db_session) -> User:
    """Create an active district admin for Medchal-Malkajgiri."""
    user = User(
        user_id=uuid.uuid4(),
        username="admin_test_medchal",
        password_hash=hash_password("testpass123"),
        role="DISTRICT_ADMIN",
        district="Medchal-Malkajgiri",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def inactive_admin(db_session) -> User:
    """Create an inactive district admin."""
    user = User(
        user_id=uuid.uuid4(),
        username="admin_inactive",
        password_hash=hash_password("testpass123"),
        role="DISTRICT_ADMIN",
        district="Sangareddy",
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def farmer_user(db_session, sample_farmer) -> User:
    """Create a user with FARMER role."""
    user = User(
        user_id=uuid.uuid4(),
        username="farmer_user",
        password_hash=hash_password("testpass123"),
        role="FARMER",
        farmer_id=sample_farmer.farmer_id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_farmer(db_session) -> Farmer:
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-ADMIN-001",
        farmer_name="Admin Test Farmer",
        mobile_number="9000000001",
        village="TestVillage",
        mandal="TestMandal",
        district="Sangareddy",
        survey_number="1",
        total_land_acres=Decimal("5.00"),
        latitude=Decimal("17.350000"),
        longitude=Decimal("78.430000"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


@pytest.fixture
def sangareddy_centre(db_session) -> ProcurementCentre:
    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-TEST-001",
        centre_name="Test Sangareddy Centre",
        agency="NAFED",
        village="TestVillage",
        mandal="TestMandal",
        district="Sangareddy",
        latitude=Decimal("17.360000"),
        longitude=Decimal("78.440000"),
        capacity=50,
        current_status="ACTIVE",
    )
    db_session.add(centre)
    db_session.commit()
    return centre


@pytest.fixture
def medchal_centre(db_session) -> ProcurementCentre:
    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-TEST-002",
        centre_name="Test Medchal Centre",
        agency="Government",
        village="TestVillage",
        mandal="TestMandal",
        district="Medchal-Malkajgiri",
        latitude=Decimal("17.630000"),
        longitude=Decimal("78.480000"),
        capacity=60,
        current_status="ACTIVE",
    )
    db_session.add(centre)
    db_session.commit()
    return centre


def _admin_login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/admin/auth/login",
        json={"username": username, "password": password},
    )


def _admin_token(user: User) -> str:
    from app.core.admin_security import create_admin_access_token
    return create_admin_access_token(user.user_id, user.username, user.district or "")


# ── Authentication Tests ─────────────────────────────────────────────────────


def test_valid_admin_login(client, admin_user):
    resp = _admin_login(client, "admin_test_sangareddy", "testpass123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["admin_id"] == str(admin_user.user_id)
    assert data["username"] == "admin_test_sangareddy"
    assert data["district"] == "Sangareddy"
    assert data["expires_in_seconds"] > 0


def test_wrong_password(client, admin_user):
    resp = _admin_login(client, "admin_test_sangareddy", "wrongpassword")
    assert resp.status_code == 401
    assert "invalid username or password" in resp.json()["detail"].lower()


def test_nonexistent_username(client, admin_user):
    resp = _admin_login(client, "nonexistent_admin", "testpass123")
    assert resp.status_code == 401
    assert "invalid username or password" in resp.json()["detail"].lower()


def test_inactive_admin_rejected(client, inactive_admin):
    resp = _admin_login(client, "admin_inactive", "testpass123")
    assert resp.status_code == 401
    assert "inactive" in resp.json()["detail"].lower()


def test_farmer_role_cannot_login_as_admin(client, farmer_user):
    resp = _admin_login(client, "farmer_user", "testpass123")
    assert resp.status_code == 401


# ── Token Validation Tests ───────────────────────────────────────────────────


def test_invalid_token_rejected(client):
    resp = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


def test_farmer_token_rejected_on_admin_endpoint(client, sample_farmer):
    """A farmer JWT must not work on admin endpoints."""
    token = create_access_token(
        sample_farmer.farmer_id,
        sample_farmer.passbook_number,
    )
    resp = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "admin" in resp.json()["detail"].lower()


def test_admin_token_works(client, admin_user):
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


# ── District Scoping Tests ───────────────────────────────────────────────────


def test_admin_sees_only_own_district_farmers(
    client, admin_user, admin_user_medchal, sample_farmer, sangareddy_centre, medchal_centre
):
    """Sangareddy admin must not see Medchal farmers."""
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/farmers",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    farmers = resp.json()
    for f in farmers:
        assert f["district"] == "Sangareddy"


def test_cross_district_centre_access_blocked(client, admin_user, medchal_centre):
    """Sangareddy admin must not see Medchal centres."""
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/centres",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    centres = resp.json()
    for c in centres:
        assert c["district"] == "Sangareddy"


def test_district_info_endpoint(client, admin_user):
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/district-info",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["district"] == "Sangareddy"
    assert data["role"] == "DISTRICT_ADMIN"
    assert data["is_active"] is True


def test_admin_dashboard_returns_rich_stats(
    client, admin_user, sample_farmer, sangareddy_centre
):
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["district"] == "Sangareddy"
    # Verify all rich stats are present
    for key in [
        "total_farmers", "active_bookings", "pending_reviews",
        "today_bookings", "farmers_in_queue", "active_centres",
        "today_procurement", "payments_processing",
        "total_centres", "total_slots", "total_bookings",
    ]:
        assert key in data, f"Missing key: {key}"
        assert isinstance(data[key], int), f"{key} should be int"


def test_admin_bookings_district_scoped(client, admin_user, medchal_centre):
    """Sangareddy admin must not see Medchal bookings."""
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/bookings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    bookings = resp.json()
    assert isinstance(bookings, list)


# ── No Auth Required ─────────────────────────────────────────────────────────


def test_admin_login_requires_no_token(client, admin_user):
    resp = _admin_login(client, "admin_test_sangareddy", "testpass123")
    assert resp.status_code == 200


def test_admin_login_empty_body(client):
    resp = client.post("/api/admin/auth/login", json={})
    assert resp.status_code == 422


# ── Existing Farmer Auth Still Works ─────────────────────────────────────────


# ── Mandal Tests (Phase 7.2) ────────────────────────────────────────────────


@pytest.fixture
def sangareddy_district(db_session) -> District:
    d = District(district_id=uuid.uuid4(), name="Sangareddy", state="Telangana")
    db_session.add(d)
    db_session.commit()
    return d


@pytest.fixture
def test_mandal(db_session, sangareddy_district) -> Mandal:
    m = Mandal(
        mandal_id=uuid.uuid4(),
        name="TestMandal",
        district_id=sangareddy_district.district_id,
    )
    db_session.add(m)
    db_session.commit()
    return m


def test_mandals_endpoint_returns_list(client, admin_user, test_mandal):
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/mandals",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    mandal = data[0]
    assert "mandal_id" in mandal
    assert "mandal_name" in mandal
    assert "farmers" in mandal
    assert "bookings" in mandal
    assert "active_queue" in mandal
    assert "procurement_completed" in mandal
    assert "payments_pending" in mandal


def test_mandal_detail_endpoint(client, admin_user, test_mandal, sample_farmer, sangareddy_centre):
    token = _admin_token(admin_user)
    resp = client.get(
        f"/api/admin/mandals/{test_mandal.mandal_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mandal_name"] == "TestMandal"
    assert data["district"] == "Sangareddy"
    assert isinstance(data["farmers"], int)
    assert isinstance(data["centres"], int)
    assert isinstance(data["recent_bookings"], list)


def test_mandal_detail_cross_district_denied(
    client, admin_user_medchal, test_mandal
):
    """Medchal admin must not access a Sangareddy mandal."""
    token = _admin_token(admin_user_medchal)
    resp = client.get(
        f"/api/admin/mandals/{test_mandal.mandal_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "not in your district" in resp.json()["detail"].lower()


def test_mandal_detail_invalid_id(client, admin_user):
    token = _admin_token(admin_user)
    resp = client.get(
        "/api/admin/mandals/not-a-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_mandal_detail_not_found(client, admin_user):
    token = _admin_token(admin_user)
    fake_id = uuid.uuid4()
    resp = client.get(
        f"/api/admin/mandals/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_farmer_auth_not_broken(client, sample_farmer):
    """Existing farmer OTP flow must not be affected by admin auth."""
    from app.services.otp_service import clear_otp_store
    clear_otp_store()

    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
        },
    )
    assert resp.status_code == 200
    otp = resp.json()["demo_otp"]

    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
            "otp": otp,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]

    clear_otp_store()
