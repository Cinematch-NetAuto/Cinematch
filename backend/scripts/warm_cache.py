"""Fill the TMDB cache in advance, so the demo still works without internet.

Run from backend/ while online, before a demo:  python -m scripts.warm_cache

Every TMDB answer is saved in the tmdb_cache table, and when TMDB cannot be
reached the backend serves the saved copy (get_or_fetch() in
app/services/movies.py). This script asks for what the main screens need,
through the same service functions the API uses, so every answer lands in
the cache:

1. the genre list;
2. discover pages 1-5 for each sort (popularity, rating, newest), 20 films a
   page: 15 pages, about 300 films;
3. a title search for every film in the movies table;
4. every user's recommendations.

Safe to run again: answers that are still fresh come from the cache, with no
TMDB call. Posters come from TMDB's image server, so offline the frontend
shows its placeholder instead.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import tmdb
from app.db import SessionLocal
from app.models import Movie, User
from app.services import movies as movie_service
from app.services import recommend as recommend_service

DISCOVER_PAGES = 5  # pages 1-5 of each sort: 15 pages, about 300 films
PER_PAGE = 20  # a whole TMDB page per request
OFFLINE_MESSAGE = (
    "TMDB cannot be reached. Check TMDB_API_TOKEN and your internet, then run it again."
)


def warm_cache(db: Session) -> int:
    """Ask for everything the main screens need; return how many TMDB answers that was.

    Answers that are still fresh come from the cache, so a second run makes no
    TMDB calls. A TmdbError (TMDB down and nothing saved) goes up to the caller.
    """
    movie_service.list_genres(db)  # saved in the genres table
    asked = 1

    for sort in movie_service.SORTS:  # popularity, rating, newest
        for page in range(1, DISCOVER_PAGES + 1):
            movie_service.discover(db, sort=sort, page=page, per_page=PER_PAGE)
            asked += 1

    titles = db.scalars(select(Movie.title).distinct().order_by(Movie.title)).all()
    for title in titles:
        if title.strip():  # TMDB has nothing to find for an empty title
            movie_service.search(db, query=title, page=1, per_page=PER_PAGE)
            asked += 1

    user_ids = db.scalars(select(User.id).order_by(User.id)).all()
    for user_id in user_ids:
        recommend_service.recommend(db, user_id)
        asked += recommend_service.CANDIDATE_PAGES  # recommend() asks for this many pages

    return asked


if __name__ == "__main__":
    with SessionLocal() as session:
        try:
            total = warm_cache(session)
        except tmdb.TmdbError:
            print(OFFLINE_MESSAGE)
            sys.exit(1)
    print(f"Cache warm: {total} TMDB answers saved for the offline demo.")
