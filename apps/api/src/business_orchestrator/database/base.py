
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

async def enable_vector_extension(connection) -> None:
    await connection.execute(
        text("CREATE EXTENSION IF NOT EXISTS vector")
    )

