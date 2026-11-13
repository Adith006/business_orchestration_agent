from uuid import UUID

import pytest
from pydantic import ValidationError

from business_orchestrator.security.dependencies import get_current_tenant
from business_orchestrator.security.schemas import AuthenticatedUser


@pytest.mark.asyncio
async def test_get_current_tenant_builds_typed_context():
    user = AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        organization_id="00000000-0000-0000-0000-000000000002",
        email="test@example.com",
        full_name="Test User",
        organization_role="owner",
    )

    tenant = await get_current_tenant(current_user=user)

    assert tenant.user_id == UUID("00000000-0000-0000-0000-000000000001")
    assert tenant.organization_id == UUID("00000000-0000-0000-0000-000000000002")
    assert tenant.organization_role == "owner"


@pytest.mark.asyncio
async def test_tenant_context_is_immutable():
    user = AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        organization_id="00000000-0000-0000-0000-000000000002",
        email="test@example.com",
        full_name="Test User",
        organization_role="owner",
    )

    tenant = await get_current_tenant(current_user=user)

    with pytest.raises(ValidationError):
        tenant.organization_id = UUID("00000000-0000-0000-0000-000000000003")