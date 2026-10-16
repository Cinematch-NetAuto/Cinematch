"""Shapes of the JSON the API sends and receives (Pydantic models).

FastAPI checks every request and response against these, and shows them on
the /docs page. Hot file: tell the team before you edit it.
"""

from pydantic import BaseModel, ConfigDict


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
    """A film's own page: the card plus runtime, tagline, genre names and cast."""

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
