"""Database engine + session factory (SQLAlchemy 2.0).

Works with SQLite out of the box and Postgres/MySQL by changing DATABASE_URL —
no code changes needed.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings

settings = get_settings()

# check_same_thread is a SQLite-only quirk; harmless to guard for it.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create tables. For a real project you'd use Alembic migrations instead."""
    from . import models  # noqa: F401  (register models on Base before create_all)
    Base.metadata.create_all(bind=engine)
