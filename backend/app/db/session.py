import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Retrieve configuration from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://neeron_user:pwd@localhost:5432/neeron"
)
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

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
