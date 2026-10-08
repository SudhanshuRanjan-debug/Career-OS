"""
Database initialization utilities.
Run migrations via Alembic — not this file.
This file is for programmatic setup in tests or first-time dev bootstrap.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.base import Base

logger = logging.getLogger(__name__)


async def create_tables(engine: AsyncEngine) -> None:
    """
    Create all tables defined in the Base metadata.
    Use ONLY in tests or local dev bootstrap.
    Production uses Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created.")


async def drop_tables(engine: AsyncEngine) -> None:
    """Drop all tables. USE ONLY IN TESTS."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables dropped.")
