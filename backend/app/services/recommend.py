"""The recommender's scoring maths.

Three small functions turn a film's genres and ratings into one score from
0.0 to 1.0. The pipeline that picks candidate films and writes the reasons is
added in a later step.
"""

MINIMUM_VOTES = 300  # below this many votes we do not fully trust a film's rating
SITE_AVERAGE = 6.5  # the typical rating across TMDB
TASTE_WEIGHT = 0.7  # how much genre fit counts in the final score
QUALITY_WEIGHT = 0.3  # how much the (weighted) rating counts


def weighted_rating(vote_average: float, vote_count: int) -> float:
    """Rate a film fairly, taking the number of voters into account.

    A 9.5 from 12 people is less trustworthy than an 8.4 from 36,000, so every
    rating is pulled towards the site average, harder when there are few votes.
    This is the formula IMDb uses for its Top 250.
    """
    weight = vote_count / (vote_count + MINIMUM_VOTES)
    return weight * vote_average + (1 - weight) * SITE_AVERAGE


def genre_match(movie_genre_ids: list[int], liked_genre_ids: list[int]) -> float:
    """How much of this film is made of genres the user likes, from 0.0 to 1.0.

    A film tagged Action + Sci-Fi, shown to someone who likes only Sci-Fi,
    scores 0.5.
    """
    if not movie_genre_ids:
        return 0.0
    liked = set(liked_genre_ids)
    hits = sum(1 for genre_id in movie_genre_ids if genre_id in liked)
    return hits / len(movie_genre_ids)


def score_movie(
    genre_ids: list[int], vote_average: float, vote_count: int, liked_genre_ids: list[int]
) -> float:
    """Final score from 0.0 to 1.0: mostly taste, partly quality.

    Taste counts more than quality: a great film in a genre you dislike is
    still not what you want tonight.
    """
    taste = genre_match(genre_ids, liked_genre_ids)
    quality = weighted_rating(vote_average, vote_count) / 10
    return TASTE_WEIGHT * taste + QUALITY_WEIGHT * quality
