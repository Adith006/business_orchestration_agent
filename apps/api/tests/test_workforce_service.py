from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from business_orchestrator.security.tenant import TenantContext
from business_orchestrator.workforce.constants import AIEmployeeStatus
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

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
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

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.get_by_id = AsyncMock(return_value=employee)

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

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.list_by_organization = AsyncMock(return_value=employees)

        service = AIEmployeeService(session)
        result = await service.list_employees(tenant)

    assert result == employees
    repository.return_value.list_by_organization.assert_awaited_once_with(
        organization_id=tenant.organization_id,
    )


@pytest.mark.asyncio
async def test_update_employee_status_allows_draft_to_configured():
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )
    employee = MagicMock()
    employee.status = AIEmployeeStatus.DRAFT.value

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.get_by_id = AsyncMock(return_value=employee)

        service = AIEmployeeService(session)
        result = await service.update_employee_status(
            employee_id=uuid4(),
            new_status=AIEmployeeStatus.CONFIGURED,
            tenant_context=tenant,
        )

    assert result is employee
    assert employee.status == AIEmployeeStatus.CONFIGURED.value
    repository.return_value.get_by_id.assert_awaited_once_with(
        employee_id=repository.return_value.get_by_id.call_args.kwargs["employee_id"],
        organization_id=tenant.organization_id,
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(employee)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (AIEmployeeStatus.CONFIGURED, AIEmployeeStatus.ACTIVE),
        (AIEmployeeStatus.ACTIVE, AIEmployeeStatus.PAUSED),
        (AIEmployeeStatus.PAUSED, AIEmployeeStatus.ACTIVE),
        (AIEmployeeStatus.DRAFT, AIEmployeeStatus.DEACTIVATED),
        (AIEmployeeStatus.CONFIGURED, AIEmployeeStatus.DEACTIVATED),
        (AIEmployeeStatus.ACTIVE, AIEmployeeStatus.DEACTIVATED),
        (AIEmployeeStatus.PAUSED, AIEmployeeStatus.DEACTIVATED),
    ],
)
async def test_update_employee_status_allows_valid_transitions(
    current_status,
    new_status,
):
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )
    employee = MagicMock()
    employee.status = current_status.value

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.get_by_id = AsyncMock(return_value=employee)

        service = AIEmployeeService(session)
        result = await service.update_employee_status(
            employee_id=uuid4(),
            new_status=new_status,
            tenant_context=tenant,
        )

    assert result is employee
    assert employee.status == new_status.value
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(employee)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (AIEmployeeStatus.DRAFT, AIEmployeeStatus.ACTIVE),
        (AIEmployeeStatus.DRAFT, AIEmployeeStatus.PAUSED),
        (AIEmployeeStatus.CONFIGURED, AIEmployeeStatus.PAUSED),
        (AIEmployeeStatus.ACTIVE, AIEmployeeStatus.CONFIGURED),
        (AIEmployeeStatus.DEACTIVATED, AIEmployeeStatus.ACTIVE),
    ],
)
async def test_update_employee_status_rejects_invalid_transitions(
    current_status,
    new_status,
):
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )
    employee = MagicMock()
    employee.status = current_status.value

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.get_by_id = AsyncMock(return_value=employee)

        service = AIEmployeeService(session)

        with pytest.raises(ValueError, match="Cannot transition"):
            await service.update_employee_status(
                employee_id=uuid4(),
                new_status=new_status,
                tenant_context=tenant,
            )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_employee_status_raises_lookup_error_when_employee_missing():
    session = AsyncMock()
    tenant = TenantContext(
        user_id=uuid4(),
        organization_id=uuid4(),
        organization_role="owner",
    )

    with patch("business_orchestrator.workforce.service.AIEmployeeRepository") as repository:
        repository.return_value.get_by_id = AsyncMock(return_value=None)

        service = AIEmployeeService(session)

        with pytest.raises(LookupError, match="AI employee not found"):
            await service.update_employee_status(
                employee_id=uuid4(),
                new_status=AIEmployeeStatus.CONFIGURED,
                tenant_context=tenant,
            )

    session.commit.assert_not_awaited()
