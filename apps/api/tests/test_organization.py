from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from business_orchestrator.database.engine import get_db_session
from business_orchestrator.main import app
from business_orchestrator.security.dependencies import get_current_user
from business_orchestrator.security.schemas import AuthenticatedUser

client = TestClient(app)


async def mock_db_session():
    yield None

async def mock_current_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        organization_id="00000000-0000-0000-0000-000000000002",
        email="test@example.com",
        full_name="Test User",
        organization_role="owner",
    )


# app.dependency_overrides[get_current_user] = mock_current_user


# app.dependency_overrides[get_db_session] = mock_db_session

@pytest.fixture(autouse=True)
def override_dependencies():
    original_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_db_session] = mock_db_session
    app.dependency_overrides[get_current_user] = mock_current_user

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


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


def test_get_organization_allows_current_tenant() -> None:
    organization_id = UUID("00000000-0000-0000-0000-000000000002")
    now = datetime.now(UTC)

    organization = MagicMock()
    organization.id = organization_id
    organization.name = "Test Organization"
    organization.slug = "test-organization"
    organization.status = "active"
    organization.created_at = now
    organization.updated_at = now

    with patch(
        "business_orchestrator.organizations.router.OrganizationService"
    ) as service_class:
        service_class.return_value.repository.get_by_id = AsyncMock(
            return_value=organization
        )

        response = client.get(
            f"/api/v1/organizations/{organization_id}"
        )

    assert response.status_code == 200


def test_get_organization_rejects_another_tenant() -> None:
    other_organization_id = UUID("00000000-0000-0000-0000-000000000003")

    response = client.get(
        f"/api/v1/organizations/{other_organization_id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found."