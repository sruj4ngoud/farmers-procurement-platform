"""Tests for root and health endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Farmer Procurement Platform API"
    assert data["version"] == "1.0.0"
    assert "/docs" in data.get("docs", "")


def test_health_endpoint(client: TestClient):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "farmer-procurement-api"
