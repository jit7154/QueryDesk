from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_healthy() -> None:
    """Test health endpoint reports ok when database is connected."""
    with patch("app.api.health.check_db_health", return_value=True):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert "version" in data


def test_health_endpoint_degraded() -> None:
    """Test health endpoint reports degraded when database is disconnected."""
    with patch("app.api.health.check_db_health", return_value=False):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"
