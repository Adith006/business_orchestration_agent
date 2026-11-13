
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from business_orchestrator.organizations.service import OrganizationService


@pytest.mark.asyncio
async def test_create_organization_assigns_owner_membership():
    session = AsyncMock()
    user_id = uuid4()
    organization = MagicMock(id=uuid4())
    membership = MagicMock()

    with (
        patch(
            "business_orchestrator.organizations.service.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.organizations.service.MembershipRepository"
        ) as membership_repo,
    ):
        organization_repo.return_value.get_by_slug = AsyncMock(
            return_value=None
        )
        organization_repo.return_value.create = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.create = AsyncMock(
            return_value=membership
        )

        service = OrganizationService(session)

        result = await service.create_organization(
            name="Test Organization",
            slug="test-organization",
            user_id=user_id,
        )

    assert result is organization

    membership_repo.return_value.create.assert_awaited_once_with(
        user_id=user_id,
        organization_id=organization.id,
        role="owner",
    )
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(organization)
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_organization_rejects_existing_slug():
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.organizations.service.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.organizations.service.MembershipRepository"
        ),
    ):
        organization_repo.return_value.get_by_slug = AsyncMock(
            return_value=MagicMock()
        )

        service = OrganizationService(session)

        with pytest.raises(
            ValueError,
            match="An organization with this slug already exists",
        ):
            await service.create_organization(
                name="Test Organization",
                slug="existing-organization",
                user_id=uuid4(),
            )

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_organization_rolls_back_on_integrity_error():
    session = AsyncMock()
    organization = MagicMock(id=uuid4())

    session.commit.side_effect = IntegrityError(
        "INSERT",
        {},
        Exception("duplicate"),
    )

    with (
        patch(
            "business_orchestrator.organizations.service.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.organizations.service.MembershipRepository"
        ) as membership_repo,
    ):
        organization_repo.return_value.get_by_slug = AsyncMock(
            return_value=None
        )
        organization_repo.return_value.create = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.create = AsyncMock()

        service = OrganizationService(session)

        with pytest.raises(
            ValueError,
            match="An organization with this slug already exists",
        ):
            await service.create_organization(
                name="Test Organization",
                slug="test-organization",
                user_id=uuid4(),
            )

    session.rollback.assert_awaited_once()
    membership_repo.return_value.create.assert_awaited_once()
