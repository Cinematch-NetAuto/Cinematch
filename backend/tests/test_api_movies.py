"""Tests for a film's own page: GET /api/movies/{tmdb_id}."""

from app import tmdb
from app.config import IMAGE_BASE

INCEPTION = 27205


def test_film_page_has_the_backdrop(client, fake_tmdb):
    answer = client.get(f"/api/movies/{INCEPTION}")
    assert answer.status_code == 200
    assert answer.json()["backdrop_url"] == f"{IMAGE_BASE}/w1280/{INCEPTION}-wide.jpg"


def test_film_without_a_backdrop_has_none(client, fake_tmdb, monkeypatch):
    plain = fake_tmdb.movie_detail
    monkeypatch.setattr(
        tmdb, "movie_detail", lambda tmdb_id: {**plain(tmdb_id), "backdrop_path": None}
    )
    assert client.get(f"/api/movies/{INCEPTION}").json()["backdrop_url"] is None


def test_unknown_film_is_404(client, fake_tmdb):
    assert client.get("/api/movies/999999").status_code == 404
