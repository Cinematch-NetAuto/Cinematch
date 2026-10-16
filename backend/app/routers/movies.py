"""Movie endpoints: genres, title search, filtered browsing and a film's page.

Routers stay thin: check the input, call the service, return its answer.
/movies/discover is declared before /movies/{tmdb_id}, so the word
"discover" is never read as a film id.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import GenreOut, MovieDetail, MoviePage
from app.services import movies as movie_service
from app.tmdb import TmdbError, TmdbNotFound

router = APIRouter(prefix="/api", tags=["movies"])

# "A database session, handed in by FastAPI for each request" (see get_db).
Db = Annotated[Session, Depends(get_db)]
Page = Annotated[int, Query(ge=1, description="Page number, from 1")]
PerPage = Annotated[int, Query(description="Results per page: 10 or 20")]
Year = Annotated[int | None, Query(ge=1874, le=2100)]

TMDB_DOWN = "TMDB cannot be reached right now. Try again in a minute."


@router.get("/genres", response_model=list[GenreOut])
def list_genres(db: Db):
    """All movie genres, for the genre filter."""
    try:
        return movie_service.list_genres(db)
    except TmdbError as error:
        raise HTTPException(status_code=502, detail=TMDB_DOWN) from error


@router.get("/movies/search", response_model=MoviePage)
def search_movies(
    db: Db,
    q: Annotated[str, Query(min_length=1, max_length=100, description="Title to search for")],
    page: Page = 1,
    per_page: PerPage = 10,
):
    """Search films by title. Answers are cached, so repeats skip TMDB."""
    try:
        return movie_service.search(db, query=q, page=page, per_page=per_page)
    except ValueError as error:  # per_page not 10 or 20, or a page past TMDB's last
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TmdbError as error:
        raise HTTPException(status_code=502, detail=TMDB_DOWN) from error


@router.get("/movies/discover", response_model=MoviePage)
def discover_movies(
    db: Db,
    genres: Annotated[
        str | None,
        Query(pattern=r"^\d+(,\d+)*$", description="Genre ids, any of them: 28,878"),
    ] = None,
    year_from: Year = None,
    year_to: Year = None,
    sort: Literal["popularity", "rating", "newest"] = "popularity",
    region: Annotated[
        str | None, Query(pattern="^[A-Za-z]{2}$", description="Country of origin, e.g. KR")
    ] = None,
    min_rating: Annotated[float | None, Query(ge=0, le=10)] = None,
    page: Page = 1,
    per_page: PerPage = 10,
):
    """Browse films by genre, years, country, minimum rating, sorted three ways."""
    if year_from and year_to and year_from > year_to:
        raise HTTPException(status_code=422, detail="year_from must not be after year_to")
    genre_ids = [int(g) for g in genres.split(",")] if genres else []
    try:
        return movie_service.discover(
            db, genre_ids, year_from, year_to, sort, region, min_rating, page, per_page
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TmdbError as error:
        raise HTTPException(status_code=502, detail=TMDB_DOWN) from error


@router.get("/movies/{tmdb_id}", response_model=MovieDetail)
def movie_detail(db: Db, tmdb_id: Annotated[int, Path(ge=1)]):
    """One film's page with its cast. Also saves the film, so it can be liked."""
    try:
        return movie_service.movie_detail(db, tmdb_id)
    except TmdbNotFound as error:
        raise HTTPException(status_code=404, detail=f"No film with id {tmdb_id}") from error
    except TmdbError as error:
        raise HTTPException(status_code=502, detail=TMDB_DOWN) from error
