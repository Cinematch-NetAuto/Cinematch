"""Tests for scripts/warm_cache.py: warming fills the cache, so the demo works offline.

Every test uses the fake TMDB from conftest.py, never the real one.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update

from app import tmdb
from app.models import Movie, TmdbCache, User, UserPreferences
from app.services import movies as movie_service
from scripts.warm_cache import warm_cache

INCEPTION = 27205


def add_film_and_user(db):
    """A saved film and a user, so the title search and the recommendations run too."""
    db.add(Movie(tmdb_id=INCEPTION, title="Inception"))
    user = User(
        email="tester@example.com", password_hash="not-a-real-hash", display_name="Tester"
    )
    db.add(user)
    db.flush()  # the database gives the user an id
    db.add(UserPreferences(user_id=user.id, preferred_genres=[18, 28, 878]))
    db.commit()


def cached_answers(db) -> int:
    """How many TMDB answers are saved in tmdb_cache."""
    return db.scalar(select(func.count()).select_from(TmdbCache))


def test_warming_asks_for_every_sort_and_fills_the_cache(db, fake_tmdb):
    add_film_and_user(db)
    warm_cache(db)
    sorts_asked = {call[1]["sort_by"] for call in fake_tmdb.calls if call[0] == "discover"}
    assert {"popularity.desc", "vote_average.desc", "primary_release_date.desc"} <= sorts_asked
    assert cached_answers(db) > 0


def test_a_second_run_makes_no_new_tmdb_calls(db, fake_tmdb):
    add_film_and_user(db)
    warm_cache(db)
    calls_after_first_run = len(fake_tmdb.calls)
    warm_cache(db)
    assert len(fake_tmdb.calls) == calls_after_first_run


def test_discover_still_works_offline_after_warming(db, fake_tmdb, monkeypatch):
    warm_cache(db)

    def offline(*args, **kwargs):
        raise tmdb.TmdbError("no internet")

    for name in ("search", "discover", "movie_detail", "genres"):
        monkeypatch.setattr(tmdb, name, offline)
    # A demo is often days after warming, so the saved copies are no longer fresh.
    db.execute(update(TmdbCache).values(fetched_at=datetime.now(UTC) - timedelta(days=2)))
    db.commit()

    page = movie_service.discover(db, sort="popularity", page=1, per_page=20)
    assert page["results"]
