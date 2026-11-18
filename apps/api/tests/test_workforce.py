from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from business_orchestrator.main import app
from business_orchestrator.security.dependencies import get_current_tenant
from business_orchestrator.security.tenant import TenantContext

client = TestClient(app)


async def mock_current_tenant() -> TenantContext:
    return TenantContext(
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        organization_id=UUID("00000000-0000-0000-0000-000000000002"),
        organization_role="owner",
    )


def test_get_ai_employee_rejects_invalid_uuid() -> None:
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        response = client.get("/api/v1/ai-employees/not-a-uuid")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 422


def test_create_ai_employee_returns_created_employee() -> None:
    now = datetime.now(UTC)
    employee = type(
        "Employee",
        (),
        {
            "id": UUID("00000000-0000-0000-0000-000000000010"),
            "organization_id": UUID("00000000-0000-0000-0000-000000000002"),
            "name": "Research Analyst",
            "role": "Research",
            "department": "Strategy",
            "description": "Conducts market research.",
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    )()

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.create_employee = AsyncMock(return_value=employee)

            response = client.post(
                "/api/v1/ai-employees",
                json={
                    "name": "Research Analyst",
                    "role": "Research",
                    "department": "Strategy",
                    "description": "Conducts market research.",
                },
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 201
    assert response.json()["name"] == "Research Analyst"
    assert response.json()["organization_id"] == str(employee.organization_id)


def test_list_ai_employees_returns_tenant_employees() -> None:
    now = datetime.now(UTC)
    employee = type(
        "Employee",
        (),
        {
            "id": UUID("00000000-0000-0000-0000-000000000010"),
            "organization_id": UUID("00000000-0000-0000-0000-000000000002"),
            "name": "Research Analyst",
            "role": "Research",
            "department": "Strategy",
            "description": None,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    )()

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.list_employees = AsyncMock(return_value=[employee])

            response = client.get("/api/v1/ai-employees")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Research Analyst"
    service_class.return_value.list_employees.assert_awaited_once()


def test_get_ai_employee_returns_employee_for_current_tenant() -> None:
    now = datetime.now(UTC)
    employee_id = UUID("00000000-0000-0000-0000-000000000010")
    employee = type(
        "Employee",
        (),
        {
            "id": employee_id,
            "organization_id": UUID("00000000-0000-0000-0000-000000000002"),
            "name": "Research Analyst",
            "role": "Research",
            "department": "Strategy",
            "description": None,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    )()

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.get_employee = AsyncMock(return_value=employee)

            response = client.get(f"/api/v1/ai-employees/{employee_id}")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200
    assert response.json()["id"] == str(employee_id)
    assert response.json()["name"] == "Research Analyst"
    service_class.return_value.get_employee.assert_awaited_once()


def test_get_ai_employee_rejects_another_tenant() -> None:
    employee_id = UUID("00000000-0000-0000-0000-000000000010")

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.get_employee = AsyncMock(return_value=None)

            response = client.get(f"/api/v1/ai-employees/{employee_id}")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 404
    assert response.json()["detail"] == "AI employee not found."
    service_class.return_value.get_employee.assert_awaited_once()


def test_update_ai_employee_status_returns_updated_employee() -> None:
    now = datetime.now(UTC)
    employee_id = UUID("00000000-0000-0000-0000-000000000010")
    employee = type(
        "Employee",
        (),
        {
            "id": employee_id,
            "organization_id": UUID("00000000-0000-0000-0000-000000000002"),
            "name": "Research Analyst",
            "role": "Research",
            "department": "Strategy",
            "description": None,
            "status": "configured",
            "created_at": now,
            "updated_at": now,
        },
    )()

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.update_employee_status = AsyncMock(return_value=employee)

            response = client.patch(
                f"/api/v1/ai-employees/{employee_id}/status",
                json={"status": "configured"},
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200
    assert response.json()["id"] == str(employee_id)
    assert response.json()["status"] == "configured"
    service_class.return_value.update_employee_status.assert_awaited_once()


def test_update_ai_employee_status_rejects_invalid_transition() -> None:
    employee_id = UUID("00000000-0000-0000-0000-000000000010")

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.update_employee_status = AsyncMock(
                side_effect=ValueError("Cannot transition AI employee from 'draft' to 'active'.")
            )

            response = client.patch(
                f"/api/v1/ai-employees/{employee_id}/status",
                json={"status": "active"},
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 409
    assert "Cannot transition" in response.json()["detail"]


def test_update_ai_employee_status_rejects_another_tenant() -> None:
    employee_id = UUID("00000000-0000-0000-0000-000000000010")

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_tenant] = mock_current_tenant

    try:
        with patch("business_orchestrator.workforce.router.AIEmployeeService") as service_class:
            service_class.return_value.update_employee_status = AsyncMock(
                side_effect=LookupError("AI employee not found.")
            )

            response = client.patch(
                f"/api/v1/ai-employees/{employee_id}/status",
                json={"status": "configured"},
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 404
    assert response.json()["detail"] == "AI employee not found."
