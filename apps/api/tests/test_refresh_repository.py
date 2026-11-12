from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from business_orchestrator.security.refresh_repository import (
    RefreshSessionRepository,
)


@pytest.mark.asyncio
async def test_create_refresh_session():
    session = AsyncMock()
    repository = RefreshSessionRepository(session)
    expires_at = datetime.now(UTC)

    result = await repository.create(
        user_id=uuid4(),
        organization_id=uuid4(),
        token_hash="a" * 64,
        expires_at=expires_at,
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(result)
    assert result.token_hash == "a" * 64


@pytest.mark.asyncio
async def test_revoke_refresh_session():
    session = AsyncMock()
    repository = RefreshSessionRepository(session)
    refresh_session = MagicMock(revoked_at=None)

    await repository.revoke(refresh_session)

    assert refresh_session.revoked_at is not None
    assert refresh_session.revoked_at.tzinfo is not None
    session.flush.assert_awaited_once()