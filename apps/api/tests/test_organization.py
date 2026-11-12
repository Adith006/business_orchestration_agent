from fastapi.testclient import TestClient

from business_orchestrator.database.engine import get_db_session
from business_orchestrator.main import app

client = TestClient(app)


async def mock_db_session():
    yield None


app.dependency_overrides[get_db_session] = mock_db_session


def test_create_organization_rejects_invalid_slug() -> None:
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "Test Organization",
            "slug": "Invalid Slug!",
        },
    )

    assert response.status_code == 422


def test_create_organization_rejects_short_name() -> None:
    response = client.post(
        "/api/v1/organizations",
        json={
            "name": "A",
            "slug": "test-organization",
        },
    )

    assert response.status_code == 422


def test_get_organization_rejects_invalid_uuid() -> None:
    response = client.get("/api/v1/organizations/not-a-uuid")

    assert response.status_code == 422