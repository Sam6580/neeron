from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# SQLite (used for tests/local dev) uses NullPool and does not accept the
# server-grade pooling kwargs, so only pass them for real database backends.
_engine_kwargs = {"pool_pre_ping": True, "future": True}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=1800,
    )

# Create async engine with production-grade connection pooling
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

# Configure session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
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


# Backwards-compatible alias used by the MQTT listener and Celery workers.
SessionLocal = async_session_factory
