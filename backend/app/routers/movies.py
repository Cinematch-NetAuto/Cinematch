"""Movie endpoints: the genre list and title search.

Routers stay thin: check the input, call the service, return its answer.
Discover (filters) and the film detail page are added in step 17.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import GenreOut, MoviePage
from app.services import movies as movie_service
from app.tmdb import TmdbError

router = APIRouter(prefix="/api", tags=["movies"])

# "A database session, handed in by FastAPI for each request" (see get_db).
Db = Annotated[Session, Depends(get_db)]

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
    page: Annotated[int, Query(ge=1, description="Page number, from 1")] = 1,
    per_page: Annotated[int, Query(description="Results per page: 10 or 20")] = 10,
):
    """Search films by title. Answers are cached, so repeats skip TMDB."""
    try:
        return movie_service.search(db, query=q, page=page, per_page=per_page)
    except ValueError as error:  # per_page not 10 or 20, or a page past TMDB's last
        raise HTTPException(status_code=422, detail=str(error)) from error
    except TmdbError as error:
        raise HTTPException(status_code=502, detail=TMDB_DOWN) from error
