"""Database schema and session management."""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import DB_PATH

# Ensure data dir exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create tables if they don't exist. Import models before calling."""
    import src.models  # noqa: F401 - register tables with Base
    Base.metadata.create_all(engine)


def get_session():
    """Return a new session. Caller should close when done."""
    return Session()


__all__ = ["Base", "Session", "engine", "init_db", "get_session"]
