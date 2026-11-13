
from fastapi.testclient import TestClient

from business_orchestrator.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_versioned_api_status_requires_authentication() -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."
