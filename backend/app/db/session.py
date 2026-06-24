import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Retrieve configuration from central settings
DATABASE_URL = settings.DATABASE_URL
POOL_SIZE = settings.DATABASE_POOL_SIZE
MAX_OVERFLOW = settings.DATABASE_MAX_OVERFLOW

# Create async engine with production-grade connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=1800,
    pool_pre_ping=True,
    future=True
)

# Configure session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection provider to spawn scoped async sessions.
    Automatically commits transactions or performs rollbacks on uncaught exceptions.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
