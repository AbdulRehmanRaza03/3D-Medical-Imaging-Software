"""SQLAlchemy database session and engine setup.

Uses a lightweight SQLite database by default for Phase 1, but the models and
session management are written to be trivially swappable to PostgreSQL via the
``DATABASE_URL`` environment variable.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _normalize_database_url(url: str) -> str:
    """Normalize the database URL for the installed driver.

    Defaults the PostgreSQL dialect to the modern ``psycopg`` (v3) driver,
    which ships as a prebuilt wheel for all supported Python versions
    (``psycopg`` is preferred over ``psycopg2``, which lacks wheels for very
    new Python releases). If a user explicitly sets ``postgresql+psycopg2://``
    we leave it untouched.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


_database_url = _normalize_database_url(settings.database_url)

_connect_args: dict = {}
if _database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Must import models before calling."""
    from app.models import study  # noqa: F401  (ensure models registered)

    Base.metadata.create_all(bind=engine)
