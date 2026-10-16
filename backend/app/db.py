"""Database connection: one engine for the app, one session per request.

The engine holds a small pool of open connections to PostgreSQL. Each request
borrows a session through get_db() and always gives it back, even on errors.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

# pool_pre_ping tests a pooled connection before use, so a database restart
# gives a fresh connection instead of an error on the next request.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: hand a session to a route, close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
