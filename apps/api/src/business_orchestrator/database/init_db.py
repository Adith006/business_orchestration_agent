
from business_orchestrator.database.base import (
    Base,
    enable_vector_extension,
)
from business_orchestrator.database.engine import engine


async def initialize_database() -> None:
    async with engine.begin() as connection:
        await enable_vector_extension(connection)
        await connection.run_sync(Base.metadata.create_all)
