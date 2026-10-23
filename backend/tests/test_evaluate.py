"""Tests for the pure parts of scripts/evaluate.py: the trials and Precision@10.

The full run needs the demo films and TMDB, so it is run by hand; its results
are in docs/evaluation.md.
"""

from scripts.evaluate import precision_at_k, trials
from scripts.seed_data import LIKE


def test_each_of_the_8_demo_likes_is_hidden_once():
    hidden = [(demo["name"], tmdb_id) for demo, tmdb_id in trials()]
    assert len(hidden) == 8
    assert len(set(hidden)) == 8


def test_dislikes_are_never_hidden():
    assert all(demo["ratings"][tmdb_id] == LIKE for demo, tmdb_id in trials())


def test_one_hit_in_the_top_10_is_a_tenth():
    assert precision_at_k([5, 1, 2, 3, 4, 6, 7, 8, 9, 10], {1}) == 0.1


def test_a_hit_below_the_top_10_does_not_count():
    assert precision_at_k(list(range(1, 21)), {11}) == 0.0


def test_a_short_list_is_still_divided_by_10():
    assert precision_at_k([1, 2], {1, 2}) == 0.2
