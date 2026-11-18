from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from business_orchestrator.security.tenant import TenantContext
from business_orchestrator.workforce.service import AIEmployeeService


@pytest.mark.asyncio
async def test_create_employee_uses_tenant_organization():
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )
    employee = MagicMock()

    with patch(
        "business_orchestrator.workforce.service.AIEmployeeRepository"
    ) as repository:
        repository.return_value.create = AsyncMock(return_value=employee)

        service = AIEmployeeService(session)

        result = await service.create_employee(
            tenant_context=tenant,
            name="Research Analyst",
            role="Research Analyst",
            department="Research",
        )

    assert result is employee
    repository.return_value.create.assert_awaited_once_with(
        organization_id=tenant.organization_id,
        name="Research Analyst",
        role="Research Analyst",
        department="Research",
        description=None,
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(employee)


@pytest.mark.asyncio
async def test_get_employee_scopes_lookup_to_tenant():
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="member",
    )
    employee_id = uuid4()
    employee = MagicMock()

    with patch(
        "business_orchestrator.workforce.service.AIEmployeeRepository"
    ) as repository:
        repository.return_value.get_by_id = AsyncMock(
            return_value=employee
        )

        service = AIEmployeeService(session)
        result = await service.get_employee(employee_id, tenant)

    assert result is employee
    repository.return_value.get_by_id.assert_awaited_once_with(
        employee_id=employee_id,
        organization_id=tenant.organization_id,
    )


@pytest.mark.asyncio
async def test_list_employees_scopes_to_tenant():
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )
    employees = [MagicMock(), MagicMock()]

    with patch(
        "business_orchestrator.workforce.service.AIEmployeeRepository"
    ) as repository:
        repository.return_value.list_by_organization = AsyncMock(
            return_value=employees
        )

        service = AIEmployeeService(session)
        result = await service.list_employees(tenant)

    assert result == employees
    repository.return_value.list_by_organization.assert_awaited_once_with(
        organization_id=tenant.organization_id,
    )