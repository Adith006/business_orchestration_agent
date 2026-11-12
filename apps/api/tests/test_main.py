
from fastapi.testclient import TestClient

from business_orchestrator.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_versioned_api_status() -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json() == {
        "status": "operational",
        "api_version": "v1",
    }
