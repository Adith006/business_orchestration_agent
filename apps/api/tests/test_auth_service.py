from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from business_orchestrator.security.service import AuthService


@pytest.mark.asyncio
async def test_register_creates_user_organization_and_owner_membership():
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    user = MagicMock(id=uuid4())
    membership = MagicMock()
    organization_id = uuid4()

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.OrganizationRepository"
        ) as org_repo,
        patch(
            "business_orchestrator.security.service.MembershipRepository"
        ) as membership_repo,
        patch(
            "business_orchestrator.security.service.hash_password",
            return_value="hashed-password",
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(return_value=None)
        user_repo.return_value.create = AsyncMock(return_value=user)

        organization = MagicMock(id=organization_id)
        org_repo.return_value.get_by_slug = AsyncMock(return_value=None)

        membership_repo.return_value.create = AsyncMock(
            return_value=membership
        )

        service = AuthService(session)

        with patch(
            "business_orchestrator.security.service.Organization",
            return_value=organization,
        ):
            result = await service.register(
                email="test@example.com",
                password="StrongPassword123",
                full_name="Test User",
                organization_name="Test Company",
                organization_slug="test-company",
            )

    assert result == (user, organization, membership)
    user_repo.return_value.create.assert_awaited_once()
    membership_repo.return_value.create.assert_awaited_once_with(
        user_id=user.id,
        organization_id=organization_id,
        role="owner",
    )
    session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_register_rejects_existing_email():
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.OrganizationRepository"
        ),
        patch(
            "business_orchestrator.security.service.MembershipRepository"
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(
            return_value=MagicMock()
        )

        service = AuthService(session)

        with pytest.raises(ValueError, match="email already exists"):
            await service.register(
                email="existing@example.com",
                password="StrongPassword123",
                full_name="Test User",
                organization_name="Test Company",
                organization_slug="test-company",
            )

    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_register_rejects_existing_organization_slug():
    session = AsyncMock()

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.OrganizationRepository"
        ) as org_repo,
        patch(
            "business_orchestrator.security.service.MembershipRepository"
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(return_value=None)
        org_repo.return_value.get_by_slug = AsyncMock(
            return_value=MagicMock()
        )

        service = AuthService(session)

        with pytest.raises(ValueError, match="organization slug is already taken"):
            await service.register(
                email="new@example.com",
                password="StrongPassword123",
                full_name="Test User",
                organization_name="Existing Company",
                organization_slug="existing-company",
            )

    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_login_accepts_valid_credentials_and_membership():
    session = AsyncMock()
    user = MagicMock(
        id=uuid4(),
        is_active=True,
        password_hash="hashed-password",
    )
    organization = MagicMock(
        id=uuid4(),
        status="active",
    )
    membership = MagicMock(status="active")

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.OrganizationRepository"
        ) as org_repo,
        patch(
            "business_orchestrator.security.service.MembershipRepository"
        ) as membership_repo,
        patch(
            "business_orchestrator.security.service.verify_password",
            return_value=True,
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(return_value=user)
        org_repo.return_value.get_by_slug = AsyncMock(
            return_value=organization
        )
        membership_repo.return_value.get_membership = AsyncMock(
            return_value=membership
        )

        service = AuthService(session)

        result = await service.login(
            email="test@example.com",
            password="StrongPassword123",
            organization_slug="test-company",
        )

    assert result == (user, organization, membership)

@pytest.mark.asyncio
async def test_login_rejects_invalid_password():
    session = AsyncMock()
    user = MagicMock(
        id=uuid4(),
        is_active=True,
        password_hash="hashed-password",
    )

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.verify_password",
            return_value=False,
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(return_value=user)

        service = AuthService(session)

        with pytest.raises(
            ValueError,
            match="Invalid email, password, or organization",
        ):
            await service.login(
                email="test@example.com",
                password="WrongPassword123",
                organization_slug="test-company",
            )

    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_login_rejects_inactive_user():
    session = AsyncMock()
    user = MagicMock(
        id=uuid4(),
        is_active=False,
        password_hash="hashed-password",
    )

    with patch(
        "business_orchestrator.security.service.UserRepository"
    ) as user_repo:
        user_repo.return_value.get_by_email = AsyncMock(return_value=user)

        service = AuthService(session)

        with pytest.raises(
            ValueError,
            match="Invalid email, password, or organization",
        ):
            await service.login(
                email="inactive@example.com",
                password="StrongPassword123",
                organization_slug="test-company",
            )

    session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_login_rejects_inactive_organization():
    session = AsyncMock()
    user = MagicMock(
        id=uuid4(),
        is_active=True,
        password_hash="hashed-password",
    )
    organization = MagicMock(
        id=uuid4(),
        status="suspended",
    )

    with (
        patch(
            "business_orchestrator.security.service.UserRepository"
        ) as user_repo,
        patch(
            "business_orchestrator.security.service.OrganizationRepository"
        ) as org_repo,
        patch(
            "business_orchestrator.security.service.verify_password",
            return_value=True,
        ),
    ):
        user_repo.return_value.get_by_email = AsyncMock(return_value=user)
        org_repo.return_value.get_by_slug = AsyncMock(
            return_value=organization
        )

        service = AuthService(session)

        with pytest.raises(
            ValueError,
            match="Invalid email, password, or organization",
        ):
            await service.login(
                email="test@example.com",
                password="StrongPassword123",
                organization_slug="test-company",
            )

    session.commit.assert_not_awaited()

def test_issue_access_token():
    user = MagicMock(id=uuid4())
    organization = MagicMock(id=uuid4())

    with patch(
        "business_orchestrator.security.service.create_access_token",
        return_value="test-access-token",
    ) as token_mock:
        service = AuthService(AsyncMock())

        token = service.issue_access_token(user, organization)

    assert token == "test-access-token"
    token_mock.assert_called_once_with(
        user_id=user.id,
        organization_id=organization.id,
    )

@pytest.mark.asyncio
async def test_issue_refresh_token():
    user = MagicMock(id=uuid4())
    organization = MagicMock(id=uuid4())

    with (
        patch(
            "business_orchestrator.security.service.generate_refresh_token",
            return_value="secure-refresh-token",
        ),
        patch(
            "business_orchestrator.security.service.hash_refresh_token",
            return_value="hashed-refresh-token",
        ) as hash_mock,
    ):
        service = AuthService(AsyncMock())
        service.refresh_sessions.create = AsyncMock()

        token = await service.issue_refresh_token(user, organization)

    assert token == "secure-refresh-token"
    hash_mock.assert_called_once_with("secure-refresh-token")
    service.refresh_sessions.create.assert_awaited_once()
    call_data = service.refresh_sessions.create.await_args.kwargs
    assert call_data["user_id"] == user.id
    assert call_data["organization_id"] == organization.id
    assert call_data["token_hash"] == "hashed-refresh-token"
    assert call_data["expires_at"].tzinfo is not None

@pytest.mark.asyncio
async def test_validate_refresh_token_accepts_valid_session():
    from datetime import UTC, datetime, timedelta

    refresh_session = MagicMock(
        revoked_at=None,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    with (
        patch(
            "business_orchestrator.security.service.hash_refresh_token",
            return_value="hashed-refresh-token",
        ),
    ):
        service = AuthService(AsyncMock())
        service.refresh_sessions.get_by_token_hash = AsyncMock(
            return_value=refresh_session
        )

        result = await service.validate_refresh_token(
            "secure-refresh-token"
        )

    assert result is refresh_session
    service.refresh_sessions.get_by_token_hash.assert_awaited_once_with(
        "hashed-refresh-token"
    )

@pytest.mark.asyncio
async def test_validate_refresh_token_rejects_revoked_session():
    from datetime import UTC, datetime, timedelta

    refresh_session = MagicMock(
        revoked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    with patch(
        "business_orchestrator.security.service.hash_refresh_token",
        return_value="hashed-refresh-token",
    ):
        service = AuthService(AsyncMock())
        service.refresh_sessions.get_by_token_hash = AsyncMock(
            return_value=refresh_session
        )

        with pytest.raises(
            ValueError,
            match="Invalid or expired refresh token",
        ):
            await service.validate_refresh_token("secure-refresh-token")

@pytest.mark.asyncio
async def test_validate_refresh_token_rejects_expired_session():
    from datetime import UTC, datetime, timedelta

    refresh_session = MagicMock(
        revoked_at=None,
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    with patch(
        "business_orchestrator.security.service.hash_refresh_token",
        return_value="hashed-refresh-token",
    ):
        service = AuthService(AsyncMock())
        service.refresh_sessions.get_by_token_hash = AsyncMock(
            return_value=refresh_session
        )

        with pytest.raises(
            ValueError,
            match="Invalid or expired refresh token",
        ):
            await service.validate_refresh_token("secure-refresh-token")

@pytest.mark.asyncio
async def test_rotate_refresh_token():
    user = MagicMock(id=uuid4(), is_active=True)
    organization = MagicMock(id=uuid4(), status="active")
    membership = MagicMock(status="active")
    old_session = MagicMock(
        user_id=user.id,
        organization_id=organization.id,
        revoked_at=None,
    )

    session = AsyncMock()

    service = AuthService(session)
    service.validate_refresh_token = AsyncMock(return_value=old_session)
    service.users.get_by_id = AsyncMock(return_value=user)
    service.organizations.get_by_id = AsyncMock(return_value=organization)
    service.memberships.get_membership = AsyncMock(return_value=membership)
    service.issue_refresh_token = AsyncMock(
        return_value="new-refresh-token"
    )
    service.issue_access_token = MagicMock(
        return_value="new-access-token"
    )

    access_token, refresh_token = await service.rotate_refresh_token(
        "old-refresh-token"
    )

    assert old_session.revoked_at is not None
    assert access_token == "new-access-token"
    assert refresh_token == "new-refresh-token"

    service.issue_refresh_token.assert_awaited_once_with(
        user,
        organization,
    )
    session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_rotate_refresh_token_rejects_revoked_token():
    session = AsyncMock()
    service = AuthService(session)

    service.validate_refresh_token = AsyncMock(
        side_effect=ValueError("Invalid or expired refresh token.")
    )
    service.users.get_by_id = AsyncMock()

    with pytest.raises(
        ValueError,
        match="Invalid or expired refresh token",
    ):
        await service.rotate_refresh_token("already-used-token")

    service.users.get_by_id.assert_not_awaited()
    service.issue_refresh_token = AsyncMock()
    service.issue_refresh_token.assert_not_awaited()
    session.commit.assert_not_awaited()