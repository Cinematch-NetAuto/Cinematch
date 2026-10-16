"""Tests for the recommender: the scoring maths, then the whole pipeline.

The pipeline tests use the shared fixtures in conftest.py. The fake TMDB
offers three films: Inception (Action, Sci-Fi), Interstellar (Adventure,
Drama, Sci-Fi) and Forrest Gump (Comedy, Drama). The test user "Tester"
picked Action, Drama and Sci-Fi at sign-up.
"""

import pytest

from app import tmdb
from app.models import UserPreferences
from app.services.recommend import (
    SITE_AVERAGE,
    genre_match,
    score_movie,
    weighted_rating,
)

ACTION, SCI_FI, DRAMA = 28, 878, 18  # TMDB genre ids


def test_many_votes_beat_few_high_votes():
    # 8.4 from 36,000 voters is more trustworthy than 9.5 from 12.
    assert weighted_rating(8.4, 36_000) > weighted_rating(9.5, 12)


def test_no_votes_gives_the_site_average():
    assert weighted_rating(9.0, 0) == pytest.approx(SITE_AVERAGE)


def test_huge_vote_count_keeps_the_real_rating():
    assert weighted_rating(7.0, 1_000_000) == pytest.approx(7.0, abs=0.01)


def test_half_the_genres_liked_scores_half():
    assert genre_match([ACTION, SCI_FI], [SCI_FI]) == 0.5


def test_all_genres_liked_scores_one():
    assert genre_match([SCI_FI], [SCI_FI, DRAMA]) == 1.0


def test_no_genres_liked_scores_zero():
    assert genre_match([ACTION], [SCI_FI]) == 0.0


def test_film_without_genres_scores_zero():
    assert genre_match([], [SCI_FI]) == 0.0


def test_liked_genre_beats_unliked_genre():
    liked = score_movie([SCI_FI], 7.5, 5_000, liked_genre_ids=[SCI_FI])
    unliked = score_movie([DRAMA], 7.5, 5_000, liked_genre_ids=[SCI_FI])
    assert liked > unliked


def test_taste_outweighs_quality():
    # An average film you like beats an excellent film you don't.
    average_liked = score_movie([SCI_FI], 6.0, 5_000, liked_genre_ids=[SCI_FI])
    excellent_unliked = score_movie([DRAMA], 9.0, 50_000, liked_genre_ids=[SCI_FI])
    assert average_liked > excellent_unliked


def test_perfect_film_in_a_liked_genre_scores_about_1():
    # 70 % taste (full match) + 30 % quality (a 10 with a million votes).
    assert score_movie([SCI_FI], 10.0, 1_000_000, [SCI_FI]) == pytest.approx(1.0, abs=0.01)


def test_quality_alone_is_worth_30_percent():
    # No genre match at all leaves only the quality part: 30 % of a perfect 10.
    assert score_movie([DRAMA], 10.0, 1_000_000, [SCI_FI]) == pytest.approx(0.3, abs=0.01)


@pytest.mark.parametrize(
    "genre_ids, vote_average, vote_count",
    [([SCI_FI], 10.0, 1_000_000), ([DRAMA], 0.0, 1_000_000), ([], 5.0, 0)],
)
def test_score_stays_between_0_and_1(genre_ids, vote_average, vote_count):
    score = score_movie(genre_ids, vote_average, vote_count, liked_genre_ids=[SCI_FI])
    assert 0.0 <= score <= 1.0


# --- The pipeline, through GET /api/me/recommendations ----------------------

INCEPTION, INTERSTELLAR, FORREST_GUMP = 27205, 157336, 13
GENRE_NAMES = {"Action", "Adventure", "Comedy", "Drama", "Science Fiction"}


def recommendations(client, headers):
    answer = client.get("/api/me/recommendations", headers=headers)
    assert answer.status_code == 200
    return answer.json()


def like(client, headers, tmdb_id, value=1):
    client.put("/api/me/likes", json={"tmdb_id": tmdb_id, "value": value}, headers=headers)


def test_a_watched_film_is_never_recommended(client, auth_headers):
    client.post("/api/me/history", json={"tmdb_id": INCEPTION}, headers=auth_headers)
    ids = [film["tmdb_id"] for film in recommendations(client, auth_headers)]
    assert INCEPTION not in ids
    assert INTERSTELLAR in ids  # the others are still offered


def test_liked_and_disliked_films_are_never_recommended(client, auth_headers):
    like(client, auth_headers, INTERSTELLAR, 1)
    like(client, auth_headers, FORREST_GUMP, -1)
    ids = [film["tmdb_id"] for film in recommendations(client, auth_headers)]
    assert ids == [INCEPTION]


def test_every_reason_names_a_real_liked_film_or_genre(client, auth_headers):
    like(client, auth_headers, INCEPTION, 1)
    for film in recommendations(client, auth_headers):
        named = film["reason"].removeprefix("Because you liked ").removeprefix("Because you like ")
        assert named == "Inception" or named in GENRE_NAMES, film["reason"]


def test_a_named_liked_film_shares_a_genre_with_the_pick(client, auth_headers):
    like(client, auth_headers, INCEPTION, 1)  # Action, Sci-Fi
    reasons = {film["title"]: film["reason"] for film in recommendations(client, auth_headers)}
    assert reasons["Interstellar"] == "Because you liked Inception"  # shares Sci-Fi
    assert reasons["Forrest Gump"] == "Because you like Drama"  # shares nothing with Inception


def test_a_new_user_gets_reasons_from_their_starter_genres(client, auth_headers):
    for film in recommendations(client, auth_headers):  # no likes yet: the cold start
        assert film["reason"].removeprefix("Because you like ") in GENRE_NAMES


def test_best_score_first(client, auth_headers):
    scores = [film["score"] for film in recommendations(client, auth_headers)]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)


def test_films_under_the_minimum_rating_are_dropped(client, auth_headers, db):
    preferences = db.query(UserPreferences).one()
    preferences.min_vote_average = 8.45  # Inception is 8.4, the other two 8.5
    db.commit()
    ids = [film["tmdb_id"] for film in recommendations(client, auth_headers)]
    assert INCEPTION not in ids and INTERSTELLAR in ids


def test_recommendations_need_a_login(client):
    assert client.get("/api/me/recommendations").status_code == 401


def test_tmdb_down_and_nothing_cached_is_502(client, auth_headers, monkeypatch):
    def down(filters, page=1):
        raise tmdb.TmdbError("no answer from TMDB (ConnectionError) after 3 attempts")

    monkeypatch.setattr(tmdb, "discover", down)
    assert client.get("/api/me/recommendations", headers=auth_headers).status_code == 502
