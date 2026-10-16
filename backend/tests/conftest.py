"""Shared test fixtures. Any test file can ask for these by name, with no setup code.

- db            a session on the TEST database, emptied before the test
- client        the API, wired to the test database, with TMDB replaced by a fake
- auth_headers  {"Authorization": "Bearer ..."} for a freshly registered user
- fake_tmdb     the fake TMDB itself, to check which calls were made

The test database is the development database's name plus "_test" (e.g.
cinematch_test) on the same server. It is created the first time it is needed.
Tests never touch the database you develop on, and never call the real TMDB.
Only tests that ask for db, client or auth_headers need PostgreSQL running.
"""

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app import security, tmdb
from app.config import DATABASE_URL
from app.db import get_db
from app.main import app
from app.models import Base
from scripts.init_db import SCHEMA_FILE

DEV_URL = make_url(DATABASE_URL)
TEST_URL = DEV_URL.set(database=f"{DEV_URL.database}_test")
TEST_SECRET = "test-secret-only-for-the-test-suite-" + "x" * 16

# --- A small fake TMDB: the same function names as app/tmdb.py ----------------

FAKE_GENRES = [
    {"id": 28, "name": "Action"},
    {"id": 12, "name": "Adventure"},
    {"id": 35, "name": "Comedy"},
    {"id": 18, "name": "Drama"},
    {"id": 878, "name": "Science Fiction"},
]


def fake_movie(tmdb_id: int, title: str, genre_ids: list[int], vote_average: float = 7.5) -> dict:
    """One film the way TMDB lists it."""
    return {
        "id": tmdb_id,
        "title": title,
        "overview": f"About {title}.",
        "release_date": "2010-07-15",
        "poster_path": f"/{tmdb_id}.jpg",
        "vote_average": vote_average,
        "vote_count": 1000,
        "popularity": 50.0,
        "genre_ids": genre_ids,
    }


FAKE_MOVIES = [
    fake_movie(27205, "Inception", [28, 878], 8.4),
    fake_movie(157336, "Interstellar", [12, 18, 878], 8.5),
    fake_movie(13, "Forrest Gump", [35, 18], 8.5),
]


class FakeTmdb:
    """Answers like TMDB, from the lists above, and remembers every call."""

    def __init__(self):
        self.calls: list[tuple] = []

    def search(self, query: str, page: int = 1) -> dict:
        self.calls.append(("search", query, page))
        found = [m for m in FAKE_MOVIES if query.lower() in m["title"].lower()]
        return {"page": page, "results": found, "total_results": len(found), "total_pages": 1}

    def discover(self, filters: dict, page: int = 1) -> dict:
        self.calls.append(("discover", dict(filters), page))
        return {"page": page, "results": FAKE_MOVIES, "total_results": 3, "total_pages": 1}

    def movie_detail(self, tmdb_id: int) -> dict:
        self.calls.append(("movie_detail", tmdb_id))
        movie = next((m for m in FAKE_MOVIES if m["id"] == tmdb_id), None)
        if movie is None:
            raise tmdb.TmdbNotFound("TMDB answered 404")
        genres = [g for g in FAKE_GENRES if g["id"] in movie["genre_ids"]]
        cast = [{"name": "An Actor", "character": "Someone", "profile_path": None}]
        return {**movie, "genres": genres, "runtime": 120, "tagline": "", "credits": {"cast": cast}}

    def genres(self) -> list[dict]:
        self.calls.append(("genres",))
        return FAKE_GENRES


# --- Fixtures used by every test (autouse) ------------------------------------


@pytest.fixture(autouse=True)
def no_real_tmdb(monkeypatch):
    """A safety net: any call that would reach the real TMDB fails the test."""

    def refuse(path, params=None):
        raise AssertionError(f"a test tried to call the real TMDB: {path}")

    monkeypatch.setattr(tmdb, "_get", refuse)


@pytest.fixture(autouse=True)
def test_secret(monkeypatch):
    """Tokens use a test secret, so tests never depend on your .env."""
    monkeypatch.setattr(security, "JWT_SECRET", TEST_SECRET)


# --- The test database ---------------------------------------------------------


@pytest.fixture(scope="session")
def test_engine():
    """An engine for the test database: created and filled from schema.sql once."""
    name = TEST_URL.database
    if not re.fullmatch(r"[A-Za-z0-9_]+_test", name or "") or name == DEV_URL.database:
        raise RuntimeError(f"refusing to use {name!r} as the test database")
    server = create_engine(DEV_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with server.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name})
        if not exists:
            conn.exec_driver_sql(f'CREATE DATABASE "{name}"')
    server.dispose()

    engine = create_engine(TEST_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.exec_driver_sql(SCHEMA_FILE.read_text(encoding="utf-8"))
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    """A session on the test database. Every table is emptied first."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with test_engine.begin() as conn:
        conn.exec_driver_sql(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def fake_tmdb(monkeypatch):
    """Replace the four TMDB functions with the fake. Returns the fake."""
    fake = FakeTmdb()
    for name in ("search", "discover", "movie_detail", "genres"):
        monkeypatch.setattr(tmdb, name, getattr(fake, name))
    return fake


@pytest.fixture
def client(db, test_engine, fake_tmdb):
    """The API as a test client: test database, fake TMDB, test secret."""
    sessions = sessionmaker(bind=test_engine)

    def test_db():
        session = sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register and log in a test user; return the header that proves it."""
    account = {
        "email": "tester@example.com",
        "password": "a long test password",
        "display_name": "Tester",
        "genre_ids": [28, 18, 878],
    }
    assert client.post("/api/auth/register", json=account).status_code == 201
    login = {"email": account["email"], "password": account["password"]}
    token = client.post("/api/auth/login", json=login).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
