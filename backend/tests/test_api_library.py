"""API tests for likes, dislikes, watch history and preferences (the /api/me routes).

They use the shared fixtures in conftest.py: the test database, a fake TMDB
with Inception (27205), Interstellar (157336) and Forrest Gump (13), and a
logged-in test user.
"""

import pytest
from sqlalchemy import func, select

from app import tmdb
from app.models import Movie, Rating

INCEPTION, INTERSTELLAR = 27205, 157336


def rate(client, headers, tmdb_id, value):
    return client.put("/api/me/likes", json={"tmdb_id": tmdb_id, "value": value}, headers=headers)


def rating_rows(db):
    return db.scalar(select(func.count()).select_from(Rating))


def patch_preferences(client, headers, **changes):
    return client.patch("/api/me/preferences", json=changes, headers=headers)


def test_liking_saves_the_film_first(client, auth_headers, db, fake_tmdb):
    assert db.get(Movie, INCEPTION) is None
    answer = rate(client, auth_headers, INCEPTION, 1)
    assert answer.status_code == 200
    assert answer.json()["title"] == "Inception"
    assert answer.json()["value"] == 1
    assert db.get(Movie, INCEPTION) is not None
    assert ("movie_detail", INCEPTION) in fake_tmdb.calls


def test_liking_twice_leaves_one_row(client, auth_headers, db, fake_tmdb):
    rate(client, auth_headers, INCEPTION, 1)
    rate(client, auth_headers, INCEPTION, 1)
    assert rating_rows(db) == 1
    assert fake_tmdb.calls.count(("movie_detail", INCEPTION)) == 1  # saved once, then reused


def test_dislike_replaces_like(client, auth_headers, db):
    rate(client, auth_headers, INCEPTION, 1)
    rate(client, auth_headers, INCEPTION, -1)
    likes = client.get("/api/me/likes", headers=auth_headers).json()
    assert [(film["tmdb_id"], film["value"]) for film in likes] == [(INCEPTION, -1)]
    assert rating_rows(db) == 1


def test_likes_are_film_cards_newest_first(client, auth_headers):
    rate(client, auth_headers, INCEPTION, 1)
    rate(client, auth_headers, INTERSTELLAR, 1)
    likes = client.get("/api/me/likes", headers=auth_headers).json()
    assert [film["title"] for film in likes] == ["Interstellar", "Inception"]
    assert likes[0]["poster_url"].endswith(f"/{INTERSTELLAR}.jpg")
    assert likes[0]["genre_ids"] == [12, 18, 878]


def test_remove_rating(client, auth_headers):
    rate(client, auth_headers, INCEPTION, 1)
    for _ in range(2):  # removing twice is not an error
        answer = client.delete("/api/me/likes", params={"tmdb_id": INCEPTION}, headers=auth_headers)
        assert answer.status_code == 204
    assert client.get("/api/me/likes", headers=auth_headers).json() == []


@pytest.mark.parametrize("value", [0, 2, -2])
def test_only_plus_or_minus_one(client, auth_headers, value):
    assert rate(client, auth_headers, INCEPTION, value).status_code == 422


def test_unknown_film_is_404(client, auth_headers):
    assert rate(client, auth_headers, 999999, 1).status_code == 404


def test_tmdb_down_and_film_not_saved_is_502(client, auth_headers, monkeypatch):
    def down(tmdb_id):
        raise tmdb.TmdbError("no answer from TMDB (ConnectionError) after 3 attempts")

    monkeypatch.setattr(tmdb, "movie_detail", down)
    assert rate(client, auth_headers, INCEPTION, 1).status_code == 502


def test_watch_history_keeps_every_watch_newest_first(client, auth_headers):
    for tmdb_id in (INCEPTION, INTERSTELLAR, INCEPTION):
        assert (
            client.post(
                "/api/me/history", json={"tmdb_id": tmdb_id}, headers=auth_headers
            ).status_code
            == 201
        )
    history = client.get("/api/me/history", headers=auth_headers).json()
    assert [film["title"] for film in history] == ["Inception", "Interstellar", "Inception"]


def test_each_user_sees_only_their_own(client, auth_headers):
    rate(client, auth_headers, INCEPTION, 1)
    other = {"email": "other@example.com", "password": "another password", "display_name": "Other",
             "genre_ids": [35, 18, 12]}  # fmt: skip
    client.post("/api/auth/register", json=other)
    token = client.post(
        "/api/auth/login", json={"email": other["email"], "password": other["password"]}
    )
    other_headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
    assert client.get("/api/me/likes", headers=other_headers).json() == []


def test_new_user_has_their_starter_genres(client, auth_headers):
    answer = client.get("/api/me/preferences", headers=auth_headers)
    assert answer.status_code == 200
    assert answer.json() == {
        "preferred_genres": [18, 28, 878],  # signed up with [28, 18, 878]
        "year_from": None,
        "year_to": None,
        "preferred_region": None,
        "min_vote_average": 0,
    }


def test_patch_changes_only_what_was_sent(client, auth_headers):
    answer = patch_preferences(client, auth_headers, preferred_region="kr")
    assert answer.status_code == 200
    assert answer.json()["preferred_region"] == "KR"  # saved in capitals
    answer = patch_preferences(client, auth_headers, min_vote_average=7.5)
    assert answer.json()["min_vote_average"] == 7.5
    assert answer.json()["preferred_region"] == "KR"  # left as it was
    assert answer.json()["preferred_genres"] == [18, 28, 878]
    assert client.get("/api/me/preferences", headers=auth_headers).json() == answer.json()


@pytest.mark.parametrize(
    "changes",
    [{"min_vote_average": 11}, {"min_vote_average": None},
     {"year_from": 2010, "year_to": 2000}, {"preferred_region": "AUS"},
     {"preferred_genres": [28, 18]}, {"preferred_genres": [28, 18, 28]}],
)  # fmt: skip
def test_bad_preferences_are_422(client, auth_headers, changes):
    assert patch_preferences(client, auth_headers, **changes).status_code == 422


def test_year_from_is_checked_against_the_saved_year_to(client, auth_headers):
    assert patch_preferences(client, auth_headers, year_to=2000).status_code == 200
    assert patch_preferences(client, auth_headers, year_from=2010).status_code == 422


def test_a_higher_minimum_rating_changes_recommendations_at_once(client, auth_headers):
    def recommended_ids():
        answer = client.get("/api/me/recommendations", headers=auth_headers)
        return [film["tmdb_id"] for film in answer.json()]

    assert INCEPTION in recommended_ids()
    patch_preferences(client, auth_headers, min_vote_average=8.45)  # Inception is 8.4
    ids = recommended_ids()
    assert INCEPTION not in ids and INTERSTELLAR in ids


@pytest.mark.parametrize(
    "method, path",
    [("get", "/api/me/likes"), ("put", "/api/me/likes"), ("delete", "/api/me/likes"),
     ("get", "/api/me/history"), ("post", "/api/me/history"),
     ("get", "/api/me/preferences"), ("patch", "/api/me/preferences")],
)  # fmt: skip
def test_every_library_route_needs_a_login(client, method, path):
    assert client.request(method, path).status_code == 401
