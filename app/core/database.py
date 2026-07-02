"""Database initialization and connection utilities."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def init_db() -> None:
    """Initialize database schemas and connections.

    Creates all tables defined in the ORM models using the shared Base.
    This runs synchronously during startup for simplicity.
    """
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///")
    sync_engine = create_engine(sync_url)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
