
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from business_orchestrator.security.dependencies import (
    get_authenticated_identity,
    get_current_user,
)


def test_get_authenticated_identity_returns_valid_uuids() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    result = get_authenticated_identity(
        {
            "sub": str(user_id),
            "org": str(organization_id),
        }
    )

    assert result == (user_id, organization_id)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"sub": "invalid-user", "org": str(uuid4())},
        {"sub": str(uuid4()), "org": "invalid-organization"},
    ],
)
def test_get_authenticated_identity_rejects_invalid_claims(
    payload: dict,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_authenticated_identity(payload)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_accepts_active_user_and_membership():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(
        id=user_id,
        is_active=True,
        email="test@example.com",
        full_name="Test User",
    )
    organization = MagicMock(status="active")
    membership = MagicMock(status="active", role="owner")

    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.get_membership = AsyncMock(
            return_value=membership
        )

        result = await get_current_user(
            payload={
                "sub": str(user_id),
                "org": str(organization_id),
            },
            session=session,
        )

    assert result.user_id == str(user_id)
    assert result.organization_id == str(organization_id)
    assert result.email == "test@example.com"
    assert result.organization_role == "owner"


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_user():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(id=user_id, is_active=False)
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock()
        membership_repo.return_value.get_membership = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401
    organization_repo.return_value.get_by_id.assert_not_awaited()
    membership_repo.return_value.get_membership.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_nonexistent_user():
    user_id = uuid4()
    organization_id = uuid4()

    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=None)
        organization_repo.return_value.get_by_id = AsyncMock()
        membership_repo.return_value.get_membership = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401
    organization_repo.return_value.get_by_id.assert_not_awaited()
    membership_repo.return_value.get_membership.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_organization():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(id=user_id, is_active=True)
    organization = MagicMock(status="suspended")
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.get_membership = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401
    membership_repo.return_value.get_membership.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_organization():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(id=user_id, is_active=True)
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock(return_value=None)
        membership_repo.return_value.get_membership = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401
    membership_repo.return_value.get_membership.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_membership():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(
        id=user_id,
        is_active=True,
        email="test@example.com",
        full_name="Test User",
    )
    organization = MagicMock(status="active")
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.get_membership = AsyncMock(
            return_value=None
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_membership():
    user_id = uuid4()
    organization_id = uuid4()

    user = MagicMock(
        id=user_id,
        is_active=True,
        email="test@example.com",
        full_name="Test User",
    )
    organization = MagicMock(status="active")
    membership = MagicMock(
        status="suspended",
        role="member",
    )

    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.dependencies.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.dependencies.OrganizationRepository"
        ) as organization_repo,
        patch(
            "business_orchestrator.security.dependencies.MembershipRepository"
        ) as membership_repo,
    ):
        user_repo.return_value.get_by_id = AsyncMock(return_value=user)
        organization_repo.return_value.get_by_id = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.get_membership = AsyncMock(
            return_value=membership
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                payload={
                    "sub": str(user_id),
                    "org": str(organization_id),
                },
                session=session,
            )

    assert exc_info.value.status_code == 401
