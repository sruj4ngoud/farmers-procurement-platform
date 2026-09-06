"""Phase 5 farmer workflow tests: dashboard -> cultivation -> booking -> token -> queue."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Booking,
    CultivationRecord,
    Farmer,
    ProcurementCentre,
    ProcurementRecord,
    QueueToken,
    Slot,
    Payment,
    Notification,
)
from app.services.otp_service import clear_otp_store


@pytest.fixture(autouse=True)
def _reset_otp_store():
    clear_otp_store()
    yield
    clear_otp_store()


@pytest.fixture
def farmer_a(db_session: Session) -> Farmer:
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-WF-A",
        farmer_name="Workflow Farmer A",
        mobile_number="9000000101",
        village="V",
        mandal="M",
        district="D",
        survey_number="1",
        total_land_acres=Decimal("8.00"),
        latitude=Decimal("17.358333"),
        longitude=Decimal("78.433333"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


@pytest.fixture
def farmer_b(db_session: Session) -> Farmer:
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-WF-B",
        farmer_name="Workflow Farmer B",
        mobile_number="9000000201",
        village="V",
        mandal="M",
        district="D",
        survey_number="2",
        total_land_acres=Decimal("5.00"),
        latitude=Decimal("17.358333"),
        longitude=Decimal("78.433333"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


@pytest.fixture
def cultivation_a(db_session: Session, farmer_a: Farmer) -> CultivationRecord:
    cultivation = CultivationRecord(
        cultivation_id=uuid.uuid4(),
        farmer_id=farmer_a.farmer_id,
        season="Rabi-2024",
        cultivated_area_acres=Decimal("6.00"),
        crop="Maize",
        quantity_produced_quintals=Decimal("100.00"),
        quantity_to_sell_quintals=Decimal("80.00"),
    )
    db_session.add(cultivation)
    db_session.commit()
    return cultivation


@pytest.fixture
def centre_a(db_session: Session) -> ProcurementCentre:
    centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-WF-A",
        centre_name="Workflow Centre A",
        agency="Government",
        village="V",
        mandal="M",
        district="D",
        latitude=Decimal("17.360000"),
        longitude=Decimal("78.440000"),
        capacity=50,
        current_status="ACTIVE",
    )
    db_session.add(centre)
    db_session.commit()
    return centre


@pytest.fixture
def slot_a(db_session: Session, centre_a: ProcurementCentre) -> Slot:
    slot = Slot(
        slot_id=uuid.uuid4(),
        centre_id=centre_a.centre_id,
        slot_date=date(2024, 9, 15),
        start_time=time(9, 0),
        end_time=time(9, 30),
        maximum_farmers=2,
        booked_farmers=0,
        is_active=True,
    )
    db_session.add(slot)
    db_session.commit()
    return slot


def _login(client, farmer) -> str:
    resp = client.post(
        "/api/auth/request-otp",
        json={
            "passbook_number": farmer.passbook_number,
            "mobile_number": farmer.mobile_number,
        },
    )
    assert resp.status_code == 200, resp.text
    otp = resp.json()["demo_otp"]
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


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_farmer_can_access_own_resources(client, farmer_a):
    token = _login(client, farmer_a)
    # The farmer's own dashboard must be reachable.
    resp = client.get(
        "/api/farmer/dashboard", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["farmer"]["passbook_number"] == farmer_a.passbook_number


def test_farmer_can_not_access_another_farmer_resources(
    client, farmer_a, farmer_b, cultivation_a, centre_a, slot_a
):
    token_b = _login(client, farmer_b)
    # Farmer B must not be able to set the quantity on Farmer A's cultivation.
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": 10.0},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Cultivation selling
# ---------------------------------------------------------------------------


def test_valid_quantity_to_sell(client, farmer_a, cultivation_a):
    token = _login(client, farmer_a)
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": 90.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["quantity_to_sell_quintals"] == 90.0


def test_zero_or_negative_quantity_to_sell_rejected(
    client, farmer_a, cultivation_a
):
    token = _login(client, farmer_a)
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": -5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_quantity_to_sell_greater_than_produced_rejected(
    client, farmer_a, cultivation_a
):
    token = _login(client, farmer_a)
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": 150.0},  # produced is 100
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "exceed" in resp.json()["detail"].lower()


def test_cannot_reduce_quantity_below_confirmed(client, farmer_a, cultivation_a, centre_a, slot_a):
    token = _login(client, farmer_a)
    # First confirmed booking consumes 50 of the 80 to-sell.
    booking_payload = {
        "cultivation_id": str(cultivation_a.cultivation_id),
        "centre_id": str(centre_a.centre_id),
        "slot_id": str(slot_a.slot_id),
        "quantity_to_sell_quintals": 50.0,
    }
    resp = client.post(
        "/api/bookings",
        json=booking_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text

    # Reducing to-sell below the 50 already booked must be rejected.
    resp = client.put(
        f"/api/farmer/cultivations/{cultivation_a.cultivation_id}/quantity-to-sell",
        json={"quantity_to_sell_quintals": 30.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "below" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Booking creation
# ---------------------------------------------------------------------------


def test_successful_booking(
    client, farmer_a, cultivation_a, centre_a, slot_a
):
    token = _login(client, farmer_a)
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 40.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["booking_number"]
    assert Decimal(body["quantity_to_sell_quintals"]) == 40
    assert body["booking_status"] == "PENDING_ADMIN_REVIEW"

    # Slot capacity must have been incremented.
    refreshed = db_get_slot(client, slot_a.slot_id)
    assert refreshed == 1  # booked_farmers incremented to 1


def _get_booking_detail(client, token, booking_id) -> dict:
    resp = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def db_get_slot(client, slot_id):
    from app.database.connection import SessionLocal
    # reuse the override session if possible by reading via public endpoint
    resp = client.get(f"/api/slots/{slot_id}")
    if resp.status_code == 404:
        return None
    return resp.json().get("booked_farmers")


def _booking_id_from(resp_json):
    return resp_json["booking_id"]


def test_quantity_exceeds_remaining_sellable(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    # Pre-book 70 so remaining sellable is 10 (80-70).
    _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 70.0)
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 20.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "remaining" in resp.json()["detail"].lower()


def test_invalid_cultivation(client, farmer_a, centre_a, slot_a):
    token = _login(client, farmer_a)
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(uuid.uuid4()),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 10.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_cultivation_belongs_to_another_farmer(
    client, farmer_a, farmer_b, centre_a, slot_a
):
    token = _login(client, farmer_a)
    # Cultivation owned by farmer_b but booking attempted by farmer_a.
    from app.models import CultivationRecord

    cult_b = CultivationRecord(
        cultivation_id=uuid.uuid4(),
        farmer_id=farmer_b.farmer_id,
        season="Rabi-2024",
        cultivated_area_acres=Decimal("4.00"),
        crop="Cotton",
        quantity_produced_quintals=Decimal("60.00"),
        quantity_to_sell_quintals=Decimal("40.00"),
    )
    db_session_via(client).add(cult_b)
    db_session_via(client).commit()
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cult_b.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 10.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_invalid_centre_slot_relationship(client, farmer_a, cultivation_a, centre_a, slot_a):
    token = _login(client, farmer_a)
    other_centre = ProcurementCentre(
        centre_id=uuid.uuid4(),
        centre_code="PC-OTHER",
        centre_name="Other Centre",
        agency="Government",
        village="V",
        mandal="M",
        district="D",
        capacity=10,
        current_status="ACTIVE",
        latitude=Decimal("17.0"),
        longitude=Decimal("78.0"),
    )
    _db = db_session_via(client)
    _db.add(other_centre)
    _db.commit()
    # slot_a belongs to centre_a, but we claim it belongs to other_centre.
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(other_centre.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 10.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_full_or_inactive_slot_rejected(
    client, farmer_a, cultivation_a, centre_a, slot_a
):
    token = _login(client, farmer_a)
    # Fill the slot to capacity (max 2).
    _make_booking(db_session_via(client), farmer_a, cultivation_a, centre_a, slot_a, 50.0)
    _make_booking(db_session_via(client), farmer_a, cultivation_a, centre_a, slot_a, 10.0)
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 5.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    assert "full" in resp.json()["detail"].lower()


def test_conflicting_duplicate_booking(
    client, farmer_a, cultivation_a, centre_a, slot_a
):
    token = _login(client, farmer_a)
    payload = {
        "cultivation_id": str(cultivation_a.cultivation_id),
        "centre_id": str(centre_a.centre_id),
        "slot_id": str(slot_a.slot_id),
        "quantity_to_sell_quintals": 40.0,
    }
    first = client.post("/api/bookings", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert first.status_code == 201
    dup = client.post("/api/bookings", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert dup.status_code == 409


def test_slot_capacity_updated_on_success(
    client, farmer_a, cultivation_a, centre_a, slot_a
):
    token = _login(client, farmer_a)
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 40.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert client.get(f"/api/slots/{slot_a.slot_id}").json()["booked_farmers"] == 1


# ---------------------------------------------------------------------------
# Token generation
# ---------------------------------------------------------------------------


def test_token_successful(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    resp = client.post(
        f"/api/bookings/{booking.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_number"] >= 1
    assert body["queue_status"] == "WAITING"
    assert body["booking_id"] == str(booking.booking_id)


def test_token_already_exists(client, farmer_a, cultivation_a, centre_a, slot_a, db_session):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    first = client.post(
        f"/api/bookings/{booking.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/bookings/{booking.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second.status_code == 409
    assert "already" in second.json()["detail"].lower()


def test_token_association_and_uniqueness(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    b1 = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 30.0)
    b2 = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 20.0)
    t1 = client.post(
        f"/api/bookings/{b1.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    t2 = client.post(
        f"/api/bookings/{b2.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert t1["token_number"] != t2["token_number"]
    assert t1["booking_id"] == str(b1.booking_id)
    assert t2["booking_id"] == str(b2.booking_id)


# ---------------------------------------------------------------------------
# Queue status
# ---------------------------------------------------------------------------


def test_queue_position(client, farmer_a, cultivation_a, centre_a, slot_a, db_session):
    token = _login(client, farmer_a)
    b1 = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 30.0)
    b2 = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 20.0)
    db_session.add_all(
        [
            QueueToken(booking_id=b1.booking_id, token_number=1, queue_status="WAITING"),
            QueueToken(booking_id=b2.booking_id, token_number=2, queue_status="WAITING"),
        ]
    )
    db_session.commit()

    resp = client.get(f"/api/queue/{b2.booking_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["position"] == 2

    resp = client.get(f"/api/queue/{b1.booking_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["position"] == 1


def test_queue_unauthorized_access_rejected(
    client, farmer_a, farmer_b, cultivation_a, centre_a, slot_a, db_session
):
    token_b = _login(client, farmer_b)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    db_session.add(QueueToken(booking_id=booking.booking_id, token_number=1, queue_status="WAITING"))
    db_session.commit()
    resp = client.get(f"/api/queue/{booking.booking_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Dashboard authenticated/unauthorized
# ---------------------------------------------------------------------------


def test_unauthorized_dashboard_rejected(client):
    resp = client.get("/api/farmer/dashboard")
    assert resp.status_code == 401


def test_dashboard_contains_active_booking(client, farmer_a, cultivation_a, centre_a, slot_a, db_session):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    db_session.add(QueueToken(booking_id=booking.booking_id, token_number=1, queue_status="WAITING"))
    db_session.commit()
    resp = client.get("/api/farmer/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["farmer"]["passbook_number"] == farmer_a.passbook_number
    assert len(data["bookings"]) == 1
    detail = data["bookings"][0]
    assert str(detail["booking_id"]) == str(booking.booking_id)
    assert detail["token"]["token_number"] == 1
    assert detail["token"]["position"] == 1


# ---------------------------------------------------------------------------
# Procurement / payment ownership
# ---------------------------------------------------------------------------


def _make_procurement_and_payment(
    db_session, booking: Booking, accepted: Decimal = Decimal("40.00")
):
    procurement = ProcurementRecord(
        procurement_id=uuid.uuid4(),
        booking_id=booking.booking_id,
        quantity_submitted_quintals=Decimal("40.00"),
        quantity_accepted_quintals=accepted,
        price_per_quintal=Decimal("2500.00"),
        procurement_status="COMPLETED",
    )
    db_session.add(procurement)
    db_session.flush()
    payment = Payment(
        payment_id=uuid.uuid4(),
        procurement_id=procurement.procurement_id,
        amount_payable=accepted * Decimal("2500.00"),
        payment_status="COMPLETED",
        transaction_reference="UPI-REF-1234",
    )
    db_session.add(payment)
    db_session.commit()
    return procurement, payment


def test_procurement_ownership_protection(
    client, farmer_a, farmer_b, cultivation_a, centre_a, slot_a, db_session
):
    token_b = _login(client, farmer_b)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    _make_procurement_and_payment(db_session, booking)
    resp = client.get(
        f"/api/procurement/{booking.booking_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


def test_procurement_own_farmer(client, farmer_a, cultivation_a, centre_a, slot_a, db_session):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    _make_procurement_and_payment(db_session, booking)
    resp = client.get(
        f"/api/procurement/{booking.booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["procurement_status"] == "COMPLETED"


def test_payment_direction_government_to_farmer(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    _make_procurement_and_payment(db_session, booking)
    resp = client.get(
        f"/api/payments/{booking.booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_status"] == "COMPLETED"
    assert data["direction"] == "GOVERNMENT_TO_FARMER"


def test_payment_ownership_protection(
    client, farmer_a, farmer_b, cultivation_a, centre_a, slot_a, db_session
):
    token_b = _login(client, farmer_b)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    _make_procurement_and_payment(db_session, booking)
    resp = client.get(
        f"/api/payments/{booking.booking_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def test_booking_confirmation_notification(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 40.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    notes = db_session.execute(
        select(Notification).where(
            Notification.farmer_id == farmer_a.farmer_id
        )
    ).scalars().all()
    assert any(n.notification_type == "BOOKING_CONFIRMED" for n in notes)


def test_token_notification(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    client.post(
        f"/api/bookings/{booking.booking_id}/token",
        headers={"Authorization": f"Bearer {token}"},
    )
    notes = db_session.execute(
        select(Notification).where(
            Notification.farmer_id == farmer_a.farmer_id,
            Notification.notification_type == "TOKEN_GENERATED",
        )
    ).scalars().all()
    assert len(notes) >= 1


def test_procurement_and_payment_notifications(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    from app.services.notification_service import (
        notify_payment_processed,
        notify_procurement_completed,
    )

    booking = _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 40.0)
    procurement, payment = _make_procurement_and_payment(db_session, booking)

    notify_procurement_completed(
        db_session, farmer_a.farmer_id, booking.booking_id,
        Decimal("40.00"), Decimal("2500.00"), commit=True,
    )
    notify_payment_processed(
        db_session, farmer_a.farmer_id, booking.booking_id,
        Decimal("100000.00"), "UPI-REF-1234", commit=True,
    )

    types = [
        n.notification_type
        for n in db_session.execute(
            select(Notification).where(
                Notification.farmer_id == farmer_a.farmer_id
            )
        ).scalars().all()
    ]
    assert "PROCUREMENT_COMPLETED" in types
    assert "PAYMENT_PROCESSED" in types


def test_mark_notification_read(client, farmer_a, db_session):
    note = Notification(
        notification_id=uuid.uuid4(),
        farmer_id=farmer_a.farmer_id,
        booking_id=None,
        notification_type="BOOKING_CONFIRMED",
        title="Hi",
        message="msg",
        is_read=False,
    )
    db_session.add(note)
    db_session.commit()
    resp = client.put(
        f"/api/notifications/{note.notification_id}/read",
        headers={"Authorization": f"Bearer {_login(client, farmer_a)}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


# ---------------------------------------------------------------------------
# Transaction rollback
# ---------------------------------------------------------------------------


def test_transaction_rollback_on_failure(
    client, farmer_a, cultivation_a, centre_a, slot_a, db_session
):
    token = _login(client, farmer_a)
    # Pre-fill remaining to 10 (to-sell 80 - 70 confirmed).
    _make_booking(db_session, farmer_a, cultivation_a, centre_a, slot_a, 70.0)

    before = client.get(f"/api/slots/{slot_a.slot_id}").json()["booked_farmers"]
    resp = client.post(
        "/api/bookings",
        json={
            "cultivation_id": str(cultivation_a.cultivation_id),
            "centre_id": str(centre_a.centre_id),
            "slot_id": str(slot_a.slot_id),
            "quantity_to_sell_quintals": 20.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
    after = client.get(f"/api/slots/{slot_a.slot_id}").json()["booked_farmers"]
    assert before == after  # slot capacity unchanged on rollback


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def db_session_via(client: TestClient):
    # The client fixture overrides get_db with a per-test session that is also
    # accessible via the same override mapping.
    from app.database.connection import get_db
    from fastapi import FastAPI

    app: FastAPI = client.app
    override = app.dependency_overrides[get_db]
    # next(override()) yields the SAME session bound to this test client.
    return next(override())


def _make_booking(
    db_session, farmer: Farmer, cultivation: CultivationRecord,
    centre: ProcurementCentre, slot: Slot, qty: Decimal | float,
) -> Booking:
    booking = Booking(
        booking_id=uuid.uuid4(),
        booking_number=f"BK-T-{uuid.uuid4().hex[:8].upper()}",
        farmer_id=farmer.farmer_id,
        cultivation_id=cultivation.cultivation_id,
        centre_id=centre.centre_id,
        slot_id=slot.slot_id,
        quantity_to_sell_quintals=Decimal(str(qty)),
        booking_status="CONFIRMED",
    )
    db_session.add(booking)
    slot.booked_farmers += 1
    db_session.commit()
    db_session.refresh(booking)
    return booking
