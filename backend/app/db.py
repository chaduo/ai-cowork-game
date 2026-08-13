from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import Settings


def create_engine_for(settings: Settings) -> Engine:
    """Create a SQLite-capable engine from application settings."""
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=connect_args, future=True)
