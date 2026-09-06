"""Phase 5 authentication tests (OTP + JWT)."""

import uuid
from decimal import Decimal
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models import Farmer
from app.services.otp_service import clear_otp_store


@pytest.fixture(autouse=True)
def _reset_otp_store():
    clear_otp_store()
    yield
    clear_otp_store()


@pytest.fixture
def sample_farmer(db_session) -> Farmer:
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-AUTH-001",
        farmer_name="Auth Test Farmer",
        mobile_number="9000000001",
        village="V",
        mandal="M",
        district="D",
        survey_number="1",
        total_land_acres=Decimal("5.00"),
        latitude=Decimal("17.350000"),
        longitude=Decimal("78.430000"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


def _request_and_get_otp(client, farmer) -> str:
    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": farmer.passbook_number,
            "mobile_number": farmer.mobile_number,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["demo_otp"]


def test_valid_farmer_otp_request(client, sample_farmer):
    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["demo_otp"] is not None
    assert len(data["demo_otp"]) == 6
    assert data["expires_in_seconds"] == 300


def test_invalid_farmer_request_otp(client):
    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": "DOES-NOT-EXIST",
            "mobile_number": "9000009999",
        },
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_request_otp_mobile_mismatch(client, sample_farmer):
    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": "9999999999",
        },
    )
    assert resp.status_code == 400
    assert "mobile" in resp.json()["detail"].lower()


def test_correct_otp_returns_jwt(client, sample_farmer):
    otp = _request_and_get_otp(client, sample_farmer)
    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
            "otp": otp,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["farmer_id"] == str(sample_farmer.farmer_id)
    assert data["expires_in_seconds"] > 0


def test_wrong_otp(client, sample_farmer):
    _request_and_get_otp(client, sample_farmer)
    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
            "otp": "000000",
        },
    )
    assert resp.status_code == 401
    assert "invalid otp" in resp.json()["detail"].lower()


def test_expired_otp(client, sample_farmer):
    from app.services import otp_service

    _request_and_get_otp(client, sample_farmer)
    # Backdate the issued OTP so verification sees it as expired.
    record = otp_service._otp_store[sample_farmer.mobile_number]
    record.expires_at = record.expires_at.replace(
        year=record.expires_at.year - 1
    )
    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
            "otp": record.otp_code,
        },
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_invalid_token_rejected(client, sample_farmer):
    resp = client.get(
        "/api/farmer/dashboard",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


def test_expired_token_rejected(client, sample_farmer):
    token = create_access_token(
        sample_farmer.farmer_id,
        sample_farmer.passbook_number,
        expires_delta=timedelta(seconds=-1),
    )
    resp = client.get(
        "/api/farmer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


def test_jwt_creation_and_use(client, sample_farmer):
    otp = _request_and_get_otp(client, sample_farmer)
    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": sample_farmer.passbook_number,
            "mobile_number": sample_farmer.mobile_number,
            "otp": otp,
        },
    )
    token = resp.json()["access_token"]
    dashboard = client.get(
        "/api/farmer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["farmer"]["passbook_number"] == sample_farmer.passbook_number


def _token_for(client, farmer) -> str:
    otp = _request_and_get_otp(client, farmer)
    resp = client.post(
        "/api/auth/verify-otp",
        json={
            "passbook_number": farmer.passbook_number,
            "mobile_number": farmer.mobile_number,
            "otp": otp,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
