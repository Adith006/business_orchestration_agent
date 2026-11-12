from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


async def enable_vector_extension(connection) -> None:
    await connection.execute(
        text("CREATE EXTENSION IF NOT EXISTS vector")
    )


# # Import models after Base is defined so SQLAlchemy registers their tables.
# from business_orchestrator.organizations.models import Organization  # noqa: E402, F401