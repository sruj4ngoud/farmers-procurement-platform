"""Tests for slots endpoints."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ProcurementCentre, Slot


@pytest.fixture
def sample_centre_for_slots(db_session: Session) -> ProcurementCentre:
    """Create a centre for slots testing."""
    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-SLOTS-001",
        centre_name="Slots Test Centre",
        agency="Government",
        village="Test Village",
        mandal="Test Mandal",
        district="Test District",
        latitude=Decimal("17.360000"),
        longitude=Decimal("78.440000"),
        capacity=50,
        current_status="ACTIVE",
    )
    db_session.add(centre)
    db_session.commit()
    return centre


@pytest.fixture
def sample_slots(db_session: Session, sample_centre_for_slots: ProcurementCentre) -> list[Slot]:
    """Create multiple slots for testing."""
    slots = [
        Slot(
            slot_id=uuid.uuid4(),
            centre_id=sample_centre_for_slots.centre_id,
            slot_date=date(2024, 9, 15),
            start_time=time(9, 0),
            end_time=time(9, 30),
            maximum_farmers=10,
            booked_farmers=5,
            is_active=True,
        ),
        Slot(
            slot_id=uuid.uuid4(),
            centre_id=sample_centre_for_slots.centre_id,
            slot_date=date(2024, 9, 15),
            start_time=time(10, 0),
            end_time=time(10, 30),
            maximum_farmers=15,
            booked_farmers=12,
            is_active=True,
        ),
    ]
    for slot in slots:
        db_session.add(slot)
    db_session.commit()
    return slots


def test_list_slots(client: TestClient, sample_slots: list[Slot]):
    """Test GET /api/slots."""
    response = client.get("/api/slots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert all("slot_id" in slot for slot in data)


def test_get_slot_by_id(client: TestClient, sample_slots: list[Slot]):
    """Test GET /api/slots/{slot_id}."""
    slot = sample_slots[0]
    response = client.get(f"/api/slots/{slot.slot_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["slot_id"] == str(slot.slot_id)
    assert data["maximum_farmers"] == slot.maximum_farmers


def test_get_slot_not_found(client: TestClient):
    """Test GET /api/slots/{slot_id} with non-existent slot."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/slots/{fake_uuid}")
    assert response.status_code == 404


def test_centre_slots_endpoint(client: TestClient, sample_centre_for_slots: ProcurementCentre, sample_slots: list[Slot]):
    """Test GET /api/centres/{centre_id}/slots."""
    response = client.get(f"/api/centres/{sample_centre_for_slots.centre_id}/slots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for slot_data in data:
        assert slot_data["centre_id"] == str(sample_centre_for_slots.centre_id)
