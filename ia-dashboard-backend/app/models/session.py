"""
app/models/session.py

Async SQLAlchemy engine and session factory.
Uses asyncpg for PostgreSQL (RNF-03 – concurrent request handling).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create engine with connection pool tuned for Cloud Run concurrency (RNF-03)
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # validates connections before use
    echo=settings.app_debug,
    # Disable prepared statement caching for PgBouncer/Supabase compatibility
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
    # inline_comments=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a database session.
    Commits on success and rolls back on any exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("db_session_error", error=str(exc))
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
    Used with Depends(get_db).
    """
    async with get_db_session() as session:
        yield session
