"""Fábrica de engine SQLAlchemy hacia el Postgres del usuario."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.settings import settings


def make_engine(conn_string: str | None = None) -> Engine:
    return create_engine(conn_string or settings.db_conn_string, pool_pre_ping=True)
