"""Tests for queue, procurement, payment, and notification endpoints."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Farmer, CultivationRecord, ProcurementCentre, Slot, Booking,
    QueueToken, ProcurementRecord, Payment, Notification
)


@pytest.fixture
def complete_workflow_setup(db_session: Session):
    """Setup complete workflow with farmer, booking, queue, procurement, payment."""
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-WORKFLOW-001",
        farmer_name="Workflow Test Farmer",
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
        centre_code="PC-WORKFLOW-001",
        centre_name="Workflow Centre",
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
        booked_farmers=1,
    )
    db_session.add(slot)

    booking = Booking(
        booking_id=uuid.uuid4(),
        booking_number="BK-WORKFLOW-001",
        farmer_id=farmer.farmer_id,
        cultivation_id=cultivation.cultivation_id,
        centre_id=centre.centre_id,
        slot_id=slot.slot_id,
        quantity_to_sell_quintals=Decimal("50.00"),
        booking_status="CONFIRMED",
    )
    db_session.add(booking)

    queue_token = QueueToken(
        queue_id=uuid.uuid4(),
        booking_id=booking.booking_id,
        token_number=1,
        queue_status="WAITING",
    )
    db_session.add(queue_token)

    procurement = ProcurementRecord(
        procurement_id=uuid.uuid4(),
        booking_id=booking.booking_id,
        quantity_submitted_quintals=Decimal("50.00"),
        quantity_accepted_quintals=Decimal("50.00"),
        price_per_quintal=Decimal("2500.00"),
        procurement_status="COMPLETED",
    )
    db_session.add(procurement)

    payment = Payment(
        payment_id=uuid.uuid4(),
        procurement_id=procurement.procurement_id,
        amount_payable=Decimal("125000.00"),
        payment_status="COMPLETED",
    )
    db_session.add(payment)

    notification = Notification(
        notification_id=uuid.uuid4(),
        farmer_id=farmer.farmer_id,
        booking_id=booking.booking_id,
        notification_type="BOOKING_CONFIRMED",
        title="Booking Confirmed",
        message="Your booking has been confirmed",
        is_read=False,
    )
    db_session.add(notification)

    db_session.commit()
    return farmer, booking, queue_token, procurement, payment, notification


def test_queue_endpoint(client: TestClient, complete_workflow_setup):
    """Test GET /api/queue/{booking_id}."""
    _, booking, queue_token, _, _, _ = complete_workflow_setup
    response = client.get(f"/api/queue/{booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["queue_id"] == str(queue_token.queue_id)
    assert data["queue_status"] == "WAITING"


def test_queue_not_found(client: TestClient):
    """Test GET /api/queue/{booking_id} with non-existent booking."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/queue/{fake_uuid}")
    assert response.status_code == 404


def test_procurement_endpoint(client: TestClient, complete_workflow_setup):
    """Test GET /api/procurement/{booking_id}."""
    _, booking, _, procurement, _, _ = complete_workflow_setup
    response = client.get(f"/api/procurement/{booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["procurement_id"] == str(procurement.procurement_id)
    assert data["procurement_status"] == "COMPLETED"


def test_procurement_not_found(client: TestClient):
    """Test GET /api/procurement/{booking_id} with no procurement."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/procurement/{fake_uuid}")
    assert response.status_code == 404


def test_payment_endpoint(client: TestClient, complete_workflow_setup):
    """Test GET /api/payments/{booking_id}."""
    _, booking, _, _, payment, _ = complete_workflow_setup
    response = client.get(f"/api/payments/{booking.booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == str(payment.payment_id)
    assert float(data["amount_payable"]) == 125000.00


def test_payment_not_found(client: TestClient):
    """Test GET /api/payments/{booking_id} with no payment."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/payments/{fake_uuid}")
    assert response.status_code == 404


def test_notifications_list(client: TestClient, complete_workflow_setup):
    """Test GET /api/notifications/{passbook_number}."""
    farmer, _, _, _, _, _ = complete_workflow_setup
    response = client.get(f"/api/notifications/{farmer.passbook_number}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["notification_type"] == "BOOKING_CONFIRMED"


def test_notifications_farmer_not_found(client: TestClient):
    """Test GET /api/notifications/{passbook_number} with non-existent farmer."""
    response = client.get("/api/notifications/NONEXISTENT")
    assert response.status_code == 404


def test_mark_notification_read(client: TestClient, complete_workflow_setup):
    """Test PUT /api/notifications/{notification_id}/read."""
    _, _, _, _, _, notification = complete_workflow_setup
    
    # Initially is_read should be False
    assert notification.is_read == False

    # Mark as read
    response = client.put(f"/api/notifications/{notification.notification_id}/read")
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] == True


def test_mark_notification_read_not_found(client: TestClient):
    """Test PUT /api/notifications/{notification_id}/read with non-existent notification."""
    fake_uuid = uuid.uuid4()
    response = client.put(f"/api/notifications/{fake_uuid}/read")
    assert response.status_code == 404
