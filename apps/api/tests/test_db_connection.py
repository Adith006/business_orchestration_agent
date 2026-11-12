import pytest
from sqlalchemy import text

from business_orchestrator.core.config import get_settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgresql_connection() -> None:
    settings = get_settings()

    if not settings.DATABASE_URL:
        pytest.skip("DATABASE_URL is not configured.")

    from business_orchestrator.database.engine import engine

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    finally:
        await engine.dispose()