"""Tests for the recommender's scoring maths."""

import pytest

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
