"""The recommender: content-based filtering plus a fair quality score.

Three small functions turn a film's genres and ratings into one score from
0.0 to 1.0. recommend() is the pipeline around them:

1. top 3 genres, from the films the user liked plus their starter genres;
2. about 60 well-rated candidates in those genres, from TMDB (cached);
3. drop films the user watched or rated, and films under their minimum rating;
4. score each film, keep the best 20;
5. give each a reason that names a real liked film or a real genre; liked
   films that fit equally well take turns, so one film does not name them all.
"""

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Movie, MovieGenre, Rating, UserPreferences, WatchHistory
from app.services import movies as movie_service

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


# --- The pipeline -----------------------------------------------------------

TOP_GENRES = 3  # how many favourite genres the candidates come from
CANDIDATE_PAGES = 3  # TMDB pages of 20: about 60 candidates
RESULTS = 20  # how many recommendations to return


def liked_films(db: Session, user_id: int) -> list[tuple[str, set[int]]]:
    """The user's liked films as (title, genre ids), most recently liked first."""
    rows = db.execute(
        select(Movie.title, Movie.tmdb_id)
        .join(Rating, Rating.movie_id == Movie.tmdb_id)
        .where(Rating.user_id == user_id, Rating.value == 1)
        .order_by(Rating.created_at.desc())
    ).all()
    ids = [tmdb_id for _, tmdb_id in rows]
    genres: dict[int, set[int]] = {tmdb_id: set() for tmdb_id in ids}
    links = db.execute(
        select(MovieGenre.movie_id, MovieGenre.genre_id).where(MovieGenre.movie_id.in_(ids))
    )
    for movie_id, genre_id in links:
        genres[movie_id].add(genre_id)
    return [(title, genres[tmdb_id]) for title, tmdb_id in rows]


def top_genres(liked: list[tuple[str, set[int]]], starter_genres: list[int]) -> list[int]:
    """The user's strongest genres: each liked film's genres and each starter genre count once."""
    counts = Counter(genre_id for _, genre_ids in liked for genre_id in genre_ids)
    counts.update(starter_genres)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))  # ties: lower id first
    return [genre_id for genre_id, _ in ranked[:TOP_GENRES]]


def reason_for(
    genre_ids: list[int],
    liked: list[tuple[str, set[int]]],
    favourites: list[int],
    genre_names: dict[int, str],
    used: Counter | None = None,
) -> str:
    """One sentence that names a real liked film, or else a real genre.

    The liked film that shares the most genres with this film is named. When
    several share the same number, the one named least often so far wins, then
    the most recent like. `used` counts how often each liked film has been
    named in this list, and this function adds the film it names.
    """
    used = Counter() if used is None else used
    film_genres = set(genre_ids)
    best_title, best_rank = None, None
    for title, liked_genres in liked:  # most recent first, so it wins a full tie
        shared = len(film_genres & liked_genres)
        rank = (shared, -used[title])
        if shared and (best_rank is None or rank > best_rank):
            best_title, best_rank = title, rank
    if best_title:
        used[best_title] += 1
        return f"Because you liked {best_title}"
    for genre_id in favourites + list(genre_ids):
        if genre_id in film_genres and genre_id in genre_names:
            return f"Because you like {genre_names[genre_id]}"
    return "Highly rated by TMDB viewers"


def give_reasons(
    picks: list[dict],
    liked: list[tuple[str, set[int]]],
    favourites: list[int],
    genre_names: dict[int, str],
) -> None:
    """Add a "reason" to each pick, in list order (best pick first).

    One counter covers the whole list, so liked films that fit equally well
    take turns: three liked animated films each name some of the tickets,
    instead of the newest like naming all of them.
    """
    used: Counter = Counter()
    for pick in picks:
        pick["reason"] = reason_for(pick["genre_ids"], liked, favourites, genre_names, used)


def recommend(db: Session, user_id: int) -> list[dict]:
    """The user's top 20 films: film cards plus a score and a reason.

    TMDB answers come through the cache, so a second call skips TMDB. A
    TmdbError (TMDB down and nothing saved) goes up to the route.
    """
    prefs = db.get(UserPreferences, user_id)
    liked = liked_films(db, user_id)
    favourites = top_genres(liked, prefs.preferred_genres if prefs else [])
    min_rating = float(prefs.min_vote_average) if prefs and prefs.min_vote_average else None

    candidates: dict[int, dict] = {}
    for page in range(1, CANDIDATE_PAGES + 1):
        result = movie_service.discover(
            db,
            genre_ids=favourites,
            year_from=prefs.year_from if prefs else None,
            year_to=prefs.year_to if prefs else None,
            sort="rating",  # well-rated films, with a vote floor
            region=prefs.preferred_region if prefs else None,
            min_rating=min_rating,
            page=page,
            per_page=20,
        )
        for card in result["results"]:
            candidates.setdefault(card["tmdb_id"], card)

    seen = set(db.scalars(select(WatchHistory.movie_id).where(WatchHistory.user_id == user_id)))
    seen |= set(db.scalars(select(Rating.movie_id).where(Rating.user_id == user_id)))
    genre_names = {genre.id: genre.name for genre in movie_service.list_genres(db)}

    picks = []
    for tmdb_id, card in candidates.items():
        if tmdb_id in seen or (min_rating and (card["vote_average"] or 0) < min_rating):
            continue
        score = score_movie(
            card["genre_ids"], card["vote_average"] or 0.0, card["vote_count"] or 0, favourites
        )
        picks.append({**card, "score": round(score, 3)})
    picks.sort(key=lambda pick: pick["score"], reverse=True)
    picks = picks[:RESULTS]
    give_reasons(picks, liked, favourites, genre_names)  # after the cut: turns over the 20 shown
    return picks
