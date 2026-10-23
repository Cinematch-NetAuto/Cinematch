"""Shapes of the JSON the API sends and receives (Pydantic models).

FastAPI checks every request and response against these, and shows them on
the /docs page. Hot file: tell the team before you edit it.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"  # something@something.something


def _clean_email(value: object) -> object:
    """Trim spaces and lowercase, so "Sam@Example.com " and "sam@example.com" match."""
    return value.strip().lower() if isinstance(value, str) else value


def _strip(value: object) -> object:
    """Trim spaces, so "  " does not count as a name."""
    return value.strip() if isinstance(value, str) else value


def _three_genres(genre_ids: list[int]) -> list[int]:
    """Keep each genre once, and insist on 3 or more different ones."""
    unique = sorted(set(genre_ids))
    if len(unique) < 3:
        raise ValueError("pick at least 3 different genres")
    return unique


class HealthOut(BaseModel):
    """Answer of GET /health."""

    status: str


class GenreOut(BaseModel):
    """One genre, e.g. {"id": 28, "name": "Action"}."""

    model_config = ConfigDict(from_attributes=True)  # can be built from a Genre row

    id: int
    name: str


class MovieCard(BaseModel):
    """The short form of a film, as shown in a grid of results."""

    tmdb_id: int
    title: str
    overview: str
    release_date: str | None  # "2010-07-15", or None when TMDB has no date
    poster_url: str | None  # full image URL, or None when there is no poster
    vote_average: float | None
    vote_count: int | None
    genre_ids: list[int]


class CastMember(BaseModel):
    """One actor in a film's cast."""

    name: str
    character: str
    profile_url: str | None  # full photo URL, or None when there is no photo


class MovieDetail(MovieCard):
    """A film's own page: the card plus backdrop, runtime, tagline, genre names and cast."""

    backdrop_url: str | None  # the wide still at the top of the film's page
    runtime: int | None  # minutes
    tagline: str
    genres: list[GenreOut]
    cast: list[CastMember]


class MoviePage(BaseModel):
    """One page of results: 10 or 20 films plus the numbers for the pager."""

    page: int
    per_page: int
    total_results: int
    total_pages: int
    results: list[MovieCard]


class UserCreate(BaseModel):
    """Sign-up form. At least 3 starter genres, so recommendations work from day one."""

    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=50)
    genre_ids: list[int] = Field(description="At least 3 different genre ids, e.g. [28, 878, 18]")

    _email = field_validator("email", mode="before")(_clean_email)
    _name = field_validator("display_name", mode="before")(_strip)
    _genres = field_validator("genre_ids")(_three_genres)


class LoginRequest(BaseModel):
    """Login form."""

    email: str
    password: str

    _email = field_validator("email", mode="before")(_clean_email)


class TokenResponse(BaseModel):
    """Answer of a successful login: the token to send as "Authorization: Bearer ..."."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """A user as the API shows them. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)  # can be built from a User row

    id: int
    email: str
    display_name: str
    content_language: str


class PreferencesOut(BaseModel):
    """A user's settings. The recommender reads them on every request."""

    model_config = ConfigDict(from_attributes=True)  # can be built from a UserPreferences row

    preferred_genres: list[int]
    year_from: int | None
    year_to: int | None
    preferred_region: str | None  # country code, e.g. "AU"
    min_vote_average: float


class PreferencesUpdate(BaseModel):
    """Changes to a user's settings. A field that is not sent stays as it is.

    year_from, year_to and preferred_region may be null (no limit).
    preferred_genres and min_vote_average may not: their default of None only
    means "not sent", and an explicit null is refused.
    """

    preferred_genres: list[int] = Field(None, description="At least 3 different genre ids")
    year_from: int | None = Field(None, ge=1874, le=2100)
    year_to: int | None = Field(None, ge=1874, le=2100)
    preferred_region: str | None = Field(None, pattern=r"^[A-Za-z]{2}$")  # e.g. "AU" or "kr"
    min_vote_average: float = Field(None, ge=0, le=10)

    _genres = field_validator("preferred_genres")(_three_genres)

    @field_validator("preferred_region")
    @classmethod
    def capitals(cls, region: str | None) -> str | None:
        """Save "kr" as "KR", the way TMDB writes country codes."""
        return region.upper() if region else region


class RatingIn(BaseModel):
    """Like (+1) or dislike (-1) one film."""

    tmdb_id: int = Field(gt=0)
    value: Literal[1, -1]


class RatedMovie(MovieCard):
    """A film card plus the user's rating and when it was given."""

    value: int  # +1 like, -1 dislike
    rated_at: datetime


class HistoryIn(BaseModel):
    """Mark one film as watched."""

    tmdb_id: int = Field(gt=0)


class WatchedMovie(MovieCard):
    """A film card plus when the user watched it."""

    watched_at: datetime


class Recommendation(MovieCard):
    """A film card plus why it was picked."""

    score: float  # 0.0 to 1.0: 0.7 x genre fit + 0.3 x fair rating
    reason: str  # e.g. "Because you liked Inception"

class GoogleLogin(BaseModel):
    credential: str
    genre_ids: list[int] | None = Field(
        default=None,
        description="At least 3 genre IDs required if this is a new user"
    )
