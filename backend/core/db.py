"""Database setup and session handling.

Uses SQLAlchemy 2.0 style with a synchronous engine for simplicity. 
Tests override DATABASE_URL to use an in-memory SQLite database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

engine = None
SessionLocal = None


def init_db(url: str | None = None) -> None:
    """Initialize the engine and session factory."""
    global engine, SessionLocal
    if url is None:
        from ..core.config import settings
        url = settings.database_url
    # For in-memory testing, we need StaticPool to share the connection.
    if url.startswith("sqlite"):
        from sqlalchemy.pool import StaticPool
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            future=True,
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    """Dependency that yields a SQLAlchemy session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all():
    """Create all tables (call after init_db)."""
    if engine is None:
        raise RuntimeError("Database not initialized")
    Base.metadata.create_all(bind=engine)