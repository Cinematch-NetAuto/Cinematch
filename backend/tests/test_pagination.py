"""Tests for to_tmdb_page(): turning our page number into a TMDB page and offset."""

import pytest

from app.services.movies import to_tmdb_page


def test_page_1_at_20_per_page_is_tmdb_page_1():
    assert to_tmdb_page(1, 20) == (1, 0)


def test_page_2_at_20_per_page_is_tmdb_page_2():
    assert to_tmdb_page(2, 20) == (2, 0)


def test_page_1_at_10_per_page_is_first_half_of_tmdb_page_1():
    assert to_tmdb_page(1, 10) == (1, 0)


def test_page_2_at_10_per_page_is_second_half_of_tmdb_page_1():
    assert to_tmdb_page(2, 10) == (1, 10)


def test_page_3_at_10_per_page_is_first_half_of_tmdb_page_2():
    assert to_tmdb_page(3, 10) == (2, 0)


def test_last_allowed_page_is_tmdb_page_500():
    assert to_tmdb_page(500, 20) == (500, 0)
    assert to_tmdb_page(1000, 10) == (500, 10)


@pytest.mark.parametrize("page, per_page", [(501, 20), (1001, 10)])
def test_page_past_tmdb_limit_is_rejected(page, per_page):
    with pytest.raises(ValueError):
        to_tmdb_page(page, per_page)


@pytest.mark.parametrize("per_page", [0, 15, 25])
def test_per_page_other_than_10_or_20_is_rejected(per_page):
    with pytest.raises(ValueError):
        to_tmdb_page(1, per_page)


def test_page_below_1_is_rejected():
    with pytest.raises(ValueError):
        to_tmdb_page(0, 20)
