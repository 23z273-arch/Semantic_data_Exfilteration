"""
database.py — SQLAlchemy setup (SQLite, WAL mode for concurrency).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings, ensure_data_dir

ensure_data_dir()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},   # Required for SQLite + threads
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    """Enable WAL mode and foreign keys for every new SQLite connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# pylint: disable=invalid-name
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for database models."""


def get_db():
    """FastAPI dependency — yields a DB session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables defined in models.py."""
    # pylint: disable=import-outside-toplevel, unused-import
    import models  # noqa: F401
    _ = models
    Base.metadata.create_all(bind=engine)
