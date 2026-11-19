
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from business_orchestrator.organizations.rbac_service import (
    OrganizationRBACService,
)


@pytest.mark.asyncio
async def test_provision_default_roles_creates_owner_and_member_roles():
    session = AsyncMock()
    organization_id = uuid4()

    owner_role = MagicMock(id=uuid4())
    member_role = MagicMock(id=uuid4())

    permissions = {
        "agent.read": MagicMock(id=uuid4()),
        "agent.create": MagicMock(id=uuid4()),
        "agent.update": MagicMock(id=uuid4()),
        "audit.read": MagicMock(id=uuid4()),
    }

    with patch(
        "business_orchestrator.organizations.rbac_service.RBACRepository"
    ) as repository_class:
        repository = repository_class.return_value

        repository.ensure_permissions = AsyncMock(
            return_value=permissions
        )
        repository.get_role = AsyncMock(
            side_effect=[None, None]
        )
        repository.create_role = AsyncMock(
            side_effect=[owner_role, member_role]
        )
        repository.assign_permissions = AsyncMock()

        service = OrganizationRBACService(session)

        result = await service.provision_default_roles(organization_id)

    assert result == (owner_role.id, member_role.id)

    assert repository.create_role.await_count == 2

    repository.assign_permissions.assert_any_await(
        role_id=owner_role.id,
        permission_ids=[
            permission.id for permission in permissions.values()
        ],
    )

    repository.assign_permissions.assert_any_await(
        role_id=member_role.id,
        permission_ids=[permissions["agent.read"].id],
    )

    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_provision_default_roles_reuses_existing_roles():
    session = AsyncMock()
    organization_id = uuid4()

    owner_role = MagicMock(id=uuid4())
    member_role = MagicMock(id=uuid4())

    permissions = {
        "agent.read": MagicMock(id=uuid4()),
    }

    with patch(
        "business_orchestrator.organizations.rbac_service.RBACRepository"
    ) as repository_class:
        repository = repository_class.return_value

        repository.ensure_permissions = AsyncMock(
            return_value=permissions
        )
        repository.get_role = AsyncMock(
            side_effect=[owner_role, member_role]
        )
        repository.create_role = AsyncMock()
        repository.assign_permissions = AsyncMock()

        service = OrganizationRBACService(session)

        result = await service.provision_default_roles(organization_id)

    assert result == (owner_role.id, member_role.id)

    repository.create_role.assert_not_awaited()
    assert repository.assign_permissions.await_count == 2
    session.flush.assert_awaited_once()
