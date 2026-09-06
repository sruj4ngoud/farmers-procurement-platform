"""Tests for centre endpoints."""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Farmer, ProcurementCentre
from app.services.distance_service import haversine_distance


@pytest.fixture
def sample_farmer_with_location(db_session: Session) -> Farmer:
    """Create a farmer with location."""
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-DIST-001",
        farmer_name="Location Farmer",
        mobile_number="9876543210",
        village="Hariharnagar",
        mandal="Tandoor",
        district="Sangareddy",
        survey_number="101-A",
        total_land_acres=Decimal("5.50"),
        latitude=Decimal("17.358333"),  # Approx Tandoor
        longitude=Decimal("78.433333"),
    )
    db_session.add(farmer)
    db_session.commit()
    return farmer


@pytest.fixture
def sample_centres(db_session: Session) -> list[ProcurementCentre]:
    """Create multiple centres for testing."""
    centres = [
        ProcurementCentre(
            centre_id=uuid.uuid4(),
            centre_code="PC-2024-001",
            centre_name="Tandoor Centre",
            agency="Government",
            village="Tandoor",
            mandal="Tandoor",
            district="Sangareddy",
            latitude=Decimal("17.360000"),
            longitude=Decimal("78.440000"),
            capacity=50,
            current_status="ACTIVE",
        ),
        ProcurementCentre(
            centre_id=uuid.uuid4(),
            centre_code="PC-2024-002",
            centre_name="Patancheru Centre",
            agency="Government",
            village="Patancheru",
            mandal="Patancheru",
            district="Sangareddy",
            latitude=Decimal("17.500000"),
            longitude=Decimal("78.500000"),
            capacity=100,
            current_status="ACTIVE",
        ),
        ProcurementCentre(
            centre_id=uuid.uuid4(),
            centre_code="PC-2024-003",
            centre_name="Faraway Centre",
            agency="Government",
            village="FarAway",
            mandal="FarAway",
            district="Other",
            latitude=Decimal("17.000000"),
            longitude=Decimal("79.000000"),
            capacity=30,
            current_status="LIMITED",
        ),
    ]
    for centre in centres:
        db_session.add(centre)
    db_session.commit()
    return centres


def test_list_centres(client: TestClient, sample_centres: list[ProcurementCentre]):
    """Test GET /api/centres."""
    response = client.get("/api/centres")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["centre_name"] in [c.centre_name for c in sample_centres]


def test_list_centres_pagination(client: TestClient, db_session: Session):
    """Test pagination on centres list."""
    # Create 15 centres
    for i in range(15):
        centre = ProcurementCentre(
            centre_id=uuid.uuid4(),
            centre_code=f"PC-BULK-{i:03d}",
            centre_name=f"Centre {i}",
            agency="Government",
            village=f"Village {i}",
            mandal=f"Mandal {i}",
            district="Test",
            latitude=Decimal("17.000000"),
            longitude=Decimal("78.000000"),
            capacity=50,
            current_status="ACTIVE",
        )
        db_session.add(centre)
    db_session.commit()

    # Test default pagination (limit=10)
    response = client.get("/api/centres")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10

    # Test with custom pagination
    response = client.get("/api/centres?limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


def test_get_centre_by_id(client: TestClient, sample_centres: list[ProcurementCentre]):
    """Test GET /api/centres/{centre_id}."""
    centre = sample_centres[0]
    response = client.get(f"/api/centres/{centre.centre_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["centre_id"] == str(centre.centre_id)
    assert data["centre_name"] == centre.centre_name


def test_get_centre_not_found(client: TestClient):
    """Test GET /api/centres/{centre_id} with non-existent centre."""
    fake_uuid = uuid.uuid4()
    response = client.get(f"/api/centres/{fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_centre_invalid_uuid(client: TestClient):
    """Test GET /api/centres/{centre_id} with invalid UUID format."""
    response = client.get("/api/centres/not-a-uuid")
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_nearby_centres(client: TestClient, sample_farmer_with_location: Farmer, sample_centres: list[ProcurementCentre]):
    """Test GET /api/centres/nearby with distance calculation."""
    response = client.get(f"/api/centres/nearby?passbook_number={sample_farmer_with_location.passbook_number}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify all responses have distance_km field
    for centre_data in data:
        assert "distance_km" in centre_data
        assert isinstance(centre_data["distance_km"], (int, float, str))


def test_nearby_centres_sorted_by_distance(client: TestClient, sample_farmer_with_location: Farmer, sample_centres: list[ProcurementCentre]):
    """Test that nearby centres are sorted by distance."""
    response = client.get(f"/api/centres/nearby?passbook_number={sample_farmer_with_location.passbook_number}")
    assert response.status_code == 200
    data = response.json()

    # Verify sorted by distance (ascending)
    distances = [float(centre["distance_km"]) for centre in data]
    assert distances == sorted(distances), "Centres should be sorted by distance"


def test_nearby_centres_farmer_not_found(client: TestClient):
    """Test GET /api/centres/nearby with non-existent farmer."""
    response = client.get("/api/centres/nearby?passbook_number=NONEXISTENT")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_nearby_centres_no_location(client: TestClient, db_session: Session):
    """Test GET /api/centres/nearby with farmer without location."""
    farmer = Farmer(
        farmer_id=uuid.uuid4(),
        passbook_number="PB-NO-LOC",
        farmer_name="No Location Farmer",
        mobile_number="9876543210",
        village="Village",
        mandal="Mandal",
        district="District",
        survey_number="101",
        total_land_acres=Decimal("5.00"),
        latitude=None,
        longitude=None,
    )
    db_session.add(farmer)
    db_session.commit()

    response = client.get(f"/api/centres/nearby?passbook_number={farmer.passbook_number}")
    assert response.status_code == 400
    assert "location not available" in response.json()["detail"].lower()


def test_haversine_distance_calculation():
    """Test Haversine distance calculation."""
    # Distance between two known points
    lat1, lon1 = Decimal("17.358333"), Decimal("78.433333")  # Tandoor
    lat2, lon2 = Decimal("17.360000"), Decimal("78.440000")  # Nearby

    distance = haversine_distance(lat1, lon1, lat2, lon2)
    assert isinstance(distance, Decimal)
    assert distance > 0  # Should be positive distance
    assert distance < 2  # Should be less than 2 km for nearby points


def test_haversine_distance_same_point():
    """Test Haversine distance for same point."""
    lat, lon = Decimal("17.358333"), Decimal("78.433333")
    distance = haversine_distance(lat, lon, lat, lon)
    assert distance == Decimal("0.00")


def test_haversine_distance_null_coordinates():
    """Test Haversine distance with null coordinates."""
    distance = haversine_distance(None, Decimal("78.0"), Decimal("17.0"), Decimal("78.0"))
    assert distance == Decimal("0")
