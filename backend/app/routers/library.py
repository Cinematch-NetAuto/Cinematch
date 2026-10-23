"""The user's own film lists (likes, dislikes, watch history) and settings.

Every route here needs a login (user: CurrentUser). A film is saved in
`movies` before it is rated or marked watched, because ratings and history
point at that table. Films come back as the same cards as search results.
The settings are the user's row in user_preferences; the recommender reads
them on every request, so a change shows in the next recommendations.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentUser, Db
from app.models import Movie, MovieGenre, Rating, UserPreferences, WatchHistory
from app.schemas import (
    HistoryIn,
    PreferencesOut,
    PreferencesUpdate,
    RatedMovie,
    RatingIn,
    WatchedMovie,
)
from app.services import movies as movie_service
from app.tmdb import TmdbError, TmdbNotFound

router = APIRouter(prefix="/api/me", tags=["library"])

HISTORY_LIMIT = 100  # the newest 100 watches are plenty for one page


def _ensure_movie(db: Session, tmdb_id: int) -> None:
    """Make sure the film is in `movies`; fetch it from TMDB and save it if not."""
    if db.get(Movie, tmdb_id) is not None:
        return
    try:
        movie_service.movie_detail(db, tmdb_id)  # fetches the film and saves it
    except TmdbNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No film with id {tmdb_id}") from error
    except TmdbError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "TMDB cannot be reached") from error


def _cards(db: Session, movie_ids: list[int]) -> dict[int, dict]:
    """Film cards for saved films, by tmdb_id: the same shape as search results."""
    movies = db.scalars(select(Movie).where(Movie.tmdb_id.in_(movie_ids))).all()
    links = db.execute(
        select(MovieGenre.movie_id, MovieGenre.genre_id).where(MovieGenre.movie_id.in_(movie_ids))
    ).all()
    genre_ids: dict[int, list[int]] = {}
    for movie_id, genre_id in links:
        genre_ids.setdefault(movie_id, []).append(genre_id)
    return {
        movie.tmdb_id: movie_service.to_card(
            {
                "id": movie.tmdb_id,
                "title": movie.title,
                "overview": movie.overview,
                "release_date": movie.release_date.isoformat() if movie.release_date else None,
                "poster_path": movie.poster_path,
                "vote_average": movie.vote_average,
                "vote_count": movie.vote_count,
                "genre_ids": sorted(genre_ids.get(movie.tmdb_id, [])),
            }
        )
        for movie in movies
    }


@router.get("/likes", response_model=list[RatedMovie])
def list_ratings(user: CurrentUser, db: Db):
    """The user's likes (+1) and dislikes (-1), newest first."""
    ratings = db.scalars(
        select(Rating).where(Rating.user_id == user.id).order_by(Rating.created_at.desc())
    ).all()
    cards = _cards(db, [rating.movie_id for rating in ratings])
    return [{**cards[r.movie_id], "value": r.value, "rated_at": r.created_at} for r in ratings]


@router.put("/likes", response_model=RatedMovie)
def rate_movie(body: RatingIn, user: CurrentUser, db: Db):
    """Like (+1) or dislike (-1) a film. Rating it again replaces the old rating."""
    _ensure_movie(db, body.tmdb_id)
    rating = db.get(Rating, (user.id, body.tmdb_id))
    if rating is None:
        rating = Rating(user_id=user.id, movie_id=body.tmdb_id, value=body.value)
        db.add(rating)
    else:  # one rating per user and film: change it, never add a second row
        rating.value = body.value
        rating.created_at = datetime.now(UTC)
    db.commit()
    card = _cards(db, [body.tmdb_id])[body.tmdb_id]
    return {**card, "value": rating.value, "rated_at": rating.created_at}


@router.delete("/likes", status_code=status.HTTP_204_NO_CONTENT)
def remove_rating(user: CurrentUser, db: Db, tmdb_id: Annotated[int, Query(gt=0)]):
    """Remove the user's rating of a film. No error if there was none."""
    rating = db.get(Rating, (user.id, tmdb_id))
    if rating is not None:
        db.delete(rating)
        db.commit()


@router.get("/history", response_model=list[WatchedMovie])
def list_history(user: CurrentUser, db: Db):
    """The films the user watched, newest first (at most 100)."""
    entries = db.scalars(
        select(WatchHistory)
        .where(WatchHistory.user_id == user.id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    cards = _cards(db, list({entry.movie_id for entry in entries}))
    return [{**cards[e.movie_id], "watched_at": e.watched_at} for e in entries]


@router.post("/history", response_model=WatchedMovie, status_code=status.HTTP_201_CREATED)
def add_to_history(body: HistoryIn, user: CurrentUser, db: Db):
    """Mark a film as watched. Watching it again adds another entry."""
    _ensure_movie(db, body.tmdb_id)
    entry = WatchHistory(user_id=user.id, movie_id=body.tmdb_id)
    db.add(entry)
    db.commit()
    card = _cards(db, [body.tmdb_id])[body.tmdb_id]
    return {**card, "watched_at": entry.watched_at}


def _preferences(db: Session, user_id: int) -> UserPreferences:
    """The user's one row in user_preferences. Sign-up makes it, so it is always there."""
    preferences = db.get(UserPreferences, user_id)
    if preferences is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No preferences saved for this user")
    return preferences


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(user: CurrentUser, db: Db):
    """The user's settings: favourite genres, years, country and minimum rating."""
    return _preferences(db, user.id)


@router.patch("/preferences", response_model=PreferencesOut)
def update_preferences(body: PreferencesUpdate, user: CurrentUser, db: Db):
    """Change only the settings that were sent, then return them all."""
    preferences = _preferences(db, user.id)
    changes = body.model_dump(exclude_unset=True)  # only the fields that were sent
    if "preferred_genres" in changes:  # the same check as sign-up
        try:
            known = {genre.id for genre in movie_service.list_genres(db)}
        except TmdbError as error:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Genre list unavailable") from error
        unknown = sorted(set(changes["preferred_genres"]) - known)
        if unknown:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown genre ids: {unknown}"
            )
    year_from = changes.get("year_from", preferences.year_from)
    year_to = changes.get("year_to", preferences.year_to)
    if year_from and year_to and year_from > year_to:  # also against the saved years
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "year_from must not be after year_to"
        )
    for field, value in changes.items():
        setattr(preferences, field, value)
    db.commit()
    return preferences
