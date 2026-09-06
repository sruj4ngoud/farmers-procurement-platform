"""Tests for bookings endpoints."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Farmer, CultivationRecord, ProcurementCentre, Slot, Booking


@pytest.fixture
def booking_test_setup(db_session: Session):
    """Setup test data for bookings."""
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-BOOKING-001",
        farmer_name="Booking Test Farmer",
        mobile_number="9876543210",
        village="Test",
        mandal="Test",
        district="Test",
        survey_number="101",
        total_land_acres=Decimal("5.00"),
    )
    db_session.add(farmer)

    cultivation = CultivationRecord(
        cultivation_id=uuid.uuid4(),
        farmer_id=farmer.farmer_id,
        season="Rabi-2024",
        cultivated_area_acres=Decimal("4.00"),
        crop="Maize",
        quantity_produced_quintals=Decimal("100.00"),
        quantity_to_sell_quintals=Decimal("80.00"),
    )
    db_session.add(cultivation)

    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-BOOKING-001",
        centre_name="Booking Centre",
        agency="Government",
        village="Test",
        mandal="Test",
        district="Test",
        capacity=50,
        current_status="ACTIVE",
    )
    db_session.add(centre)

    slot = Slot(
        slot_id=uuid.uuid4(),
        centre_id=centre.centre_id,
        slot_date=date(2024, 9, 15),
        start_time=time(9, 0),
        end_time=time(9, 30),
        maximum_farmers=10,
        booked_farmers=2,
    )
    db_session.add(slot)
    db_session.commit()

    return farmer, cultivation, centre, slot


@pytest.fixture
def sample_bookings(db_session: Session, booking_test_setup) -> list[Booking]:
    """Create sample bookings."""
    farmer, cultivation, centre, slot = booking_test_setup
    bookings = [
        Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-001-2024",
            farmer_id=farmer.farmer_id,
            cultivation_id=cultivation.cultivation_id,
            centre_id=centre.centre_id,
            slot_id=slot.slot_id,
            quantity_to_sell_quintals=Decimal("50.00"),
            booking_status="CONFIRMED",
        ),
        Booking(
            booking_id=uuid.uuid4(),
            booking_number="BK-002-2024",
            farmer_id=farmer.farmer_id,
            cultivation_id=cultivation.cultivation_id,
            centre_id=centre.centre_id,
            slot_id=slot.slot_id,
            quantity_to_sell_quintals=Decimal("30.00"),
            booking_status="CONFIRMED",
        ),
    ]
    for booking in bookings:
        db_session.add(booking)
    db_session.commit()
    return bookings


def test_list_bookings(client: TestClient, sample_bookings: list[Booking]):
    """Test GET /api/bookings."""
    response = client.get("/api/bookings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_get_booking_by_id(client: TestClient, sample_bookings: list[Booking]):
    """Test GET /api/bookings/{booking_id}."""
    booking = sample_bookings[0]
    response = client.get(f"/api/bookings/{booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["booking_id"] == str(booking.booking_id)
    assert data["booking_number"] == "BK-001-2024"


def test_get_booking_not_found(client: TestClient):
    """Test GET /api/bookings/{booking_id} with non-existent booking."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/bookings/{fake_uuid}")
    assert response.status_code == 404
