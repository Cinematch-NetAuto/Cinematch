"""The recommendations endpoint: 20 films picked for the logged-in user.

The work happens in services/recommend.py; this route only checks the login
and turns a TMDB failure into a clear answer.
"""

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, Db
from app.schemas import Recommendation
from app.services import recommend as recommend_service
from app.tmdb import TmdbError

router = APIRouter(prefix="/api/me", tags=["recommendations"])


@router.get("/recommendations", response_model=list[Recommendation])
def recommendations(user: CurrentUser, db: Db):
    """Up to 20 films for you, best first, each with a score and a reason."""
    try:
        return recommend_service.recommend(db, user.id)
    except TmdbError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "TMDB cannot be reached") from error
