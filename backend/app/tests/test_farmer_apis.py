"""Tests for farmer endpoints."""

import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Farmer, CultivationRecord, Booking, Slot, ProcurementCentre


@pytest.fixture
def sample_farmer(db_session: Session) -> Farmer:
    """Create a sample farmer for testing."""
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-2024-001",
        farmer_name="Ramesh Kumar",
        mobile_number="9876543210",
        village="Hariharnagar",
        mandal="Tandoor",
        district="Sangareddy",
        survey_number="101-A",
        total_land_acres=Decimal("5.50"),
        latitude=Decimal("17.358333"),
        longitude=Decimal("78.433333"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


@pytest.fixture
def sample_cultivation(db_session: Session, sample_farmer: Farmer) -> CultivationRecord:
    """Create a sample cultivation record."""
    cultivation = CultivationRecord(
        cultivation_id=uuid.uuid4(),
        farmer_id=sample_farmer.farmer_id,
        season="Rabi-2024",
        cultivated_area_acres=Decimal("4.50"),
        crop="Maize",
        quantity_produced_quintals=Decimal("90.00"),
        quantity_to_sell_quintals=Decimal("75.00"),
    )
    db_session.add(cultivation)
    db_session.commit()
    return cultivation


@pytest.fixture
def sample_centre(db_session: Session) -> ProcurementCentre:
    """Create a sample procurement centre."""
    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-2024-001",
        centre_name="Tandoor Procurement Centre",
        agency="Government",
        village="Tandoor",
        mandal="Tandoor",
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
def sample_slot(db_session: Session, sample_centre: ProcurementCentre) -> Slot:
    """Create a sample slot."""
    from datetime import date, time
    slot = Slot(
        slot_id=uuid.uuid4(),
        centre_id=sample_centre.centre_id,
        slot_date=date(2024, 9, 15),
        start_time=time(9, 0, 0),
        end_time=time(9, 30, 0),
        maximum_farmers=10,
        booked_farmers=3,
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    return slot


@pytest.fixture
def sample_booking(db_session: Session, sample_farmer: Farmer, sample_cultivation: CultivationRecord, sample_centre: ProcurementCentre, sample_slot: Slot) -> Booking:
    """Create a sample booking."""
    booking = Booking(
        booking_id=uuid.uuid4(),
        booking_number="BK-2024-001",
        farmer_id=sample_farmer.farmer_id,
        cultivation_id=sample_cultivation.cultivation_id,
        centre_id=sample_centre.centre_id,
        slot_id=sample_slot.slot_id,
        quantity_to_sell_quintals=Decimal("50.00"),
        booking_status="CONFIRMED",
    )
    db_session.add(booking)
    db_session.commit()
    return booking


def test_get_farmer_by_passbook_number(client: TestClient, sample_farmer: Farmer):
    """Test GET /api/farmers/{passbook_number}."""
    response = client.get(f"/api/farmers/{sample_farmer.passbook_number}")
    assert response.status_code == 200
    data = response.json()
    assert data["passbook_number"] == sample_farmer.passbook_number
    assert data["farmer_name"] == sample_farmer.farmer_name
    assert data["mobile_number"] == sample_farmer.mobile_number


def test_get_farmer_not_found(client: TestClient):
    """Test GET /api/farmers/{passbook_number} with non-existent farmer."""
    response = client.get("/api/farmers/NONEXISTENT-PB")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_farmer_cultivations(client: TestClient, sample_farmer: Farmer, sample_cultivation: CultivationRecord):
    """Test GET /api/farmers/{passbook_number}/cultivations."""
    response = client.get(f"/api/farmers/{sample_farmer.passbook_number}/cultivations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cultivation_id"] == str(sample_cultivation.cultivation_id)
    assert data[0]["crop"] == "Maize"


def test_get_farmer_cultivations_with_pagination(client: TestClient, sample_farmer: Farmer, db_session: Session):
    """Test pagination on cultivations endpoint."""
    # Create multiple cultivations
    for i in range(15):
        cultivation = CultivationRecord(
            cultivation_id=uuid.uuid4(),
            farmer_id=sample_farmer.farmer_id,
            season=f"Rabi-202{4+i}",
            cultivated_area_acres=Decimal("4.50"),
            crop=f"Crop-{i}",
            quantity_produced_quintals=Decimal("90.00"),
            quantity_to_sell_quintals=Decimal("75.00"),
        )
        db_session.add(cultivation)
    db_session.commit()

    # Test default pagination
    response = client.get(f"/api/farmers/{sample_farmer.passbook_number}/cultivations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10  # Default limit

    # Test with limit and offset
    response = client.get(
        f"/api/farmers/{sample_farmer.passbook_number}/cultivations?limit=5&offset=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


def test_get_farmer_bookings(client: TestClient, sample_farmer: Farmer, sample_booking: Booking):
    """Test GET /api/farmers/{passbook_number}/bookings."""
    response = client.get(f"/api/farmers/{sample_farmer.passbook_number}/bookings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["booking_number"] == "BK-2024-001"
    assert data[0]["booking_status"] == "CONFIRMED"


def test_get_farmer_bookings_empty(client: TestClient, sample_farmer: Farmer):
    """Test GET /api/farmers/{passbook_number}/bookings with no bookings."""
    response = client.get(f"/api/farmers/{sample_farmer.passbook_number}/bookings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
