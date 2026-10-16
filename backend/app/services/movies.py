"""Movie logic: paging, caching, search, discover filters and film details.

get_or_fetch() is the cache in front of TMDB: a saved answer younger than
CACHE_HOURS is reused, so the same search twice costs one TMDB call. When
TMDB cannot be reached, an old saved copy is better than an error.
"""

import json
import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from math import ceil
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import tmdb
from app.config import CACHE_HOURS, IMAGE_BASE
from app.models import Genre, Movie, MovieGenre, TmdbCache

logger = logging.getLogger(__name__)

TMDB_PAGE_SIZE = 20  # TMDB always returns exactly 20 results per page
TMDB_MAX_PAGE = 500  # TMDB refuses any page number above 500
POSTER_SIZE = "w342"  # TMDB image width that suits a poster grid
PROFILE_SIZE = "w185"  # TMDB image width for cast photos
CAST_SIZE = 10  # actors shown on a film's page
MIN_VOTES = 200  # rating filters ignore films with fewer votes, or 1-vote films win

# Our sort names -> TMDB's sort_by values
SORTS = {
    "popularity": "popularity.desc",
    "rating": "vote_average.desc",
    "newest": "primary_release_date.desc",
}


def to_tmdb_page(page: int, per_page: int) -> tuple[int, int]:
    """Work out which TMDB page holds our page, and where our page starts in it.

    Returns (tmdb_page, offset). Example: our page 4 at 10 per page is (2, 10),
    the second half of TMDB page 2.
    """
    if per_page not in (10, 20):
        raise ValueError("per_page must be 10 or 20")
    if page < 1:
        raise ValueError("page must be 1 or more")

    first_result = (page - 1) * per_page  # position of our first film in TMDB's full list
    tmdb_page = first_result // TMDB_PAGE_SIZE + 1
    offset = first_result % TMDB_PAGE_SIZE

    if tmdb_page > TMDB_MAX_PAGE:
        raise ValueError(f"TMDB has no page {tmdb_page}; the last page is {TMDB_MAX_PAGE}")
    return tmdb_page, offset


def cache_key(kind: str, *parts: object) -> str:
    """Build a cache key such as "search:inception:1" (case and spaces ignored)."""
    return ":".join([kind, *(str(part).strip().lower() for part in parts)])


def get_or_fetch(db: Session, key: str, fetch: Callable[[], dict]) -> dict:
    """Return TMDB's answer for `key`, from the cache when it is fresh.

    - a saved copy younger than CACHE_HOURS: use it, no TMDB call;
    - otherwise call fetch() (a tmdb.py function), save the answer, return it;
    - TMDB fails but an older copy is saved: return the old copy;
    - TMDB fails and nothing is saved: the TmdbError goes up to the route.
    """
    saved = db.get(TmdbCache, key)
    now = datetime.now(UTC)
    if saved is not None and now - saved.fetched_at < timedelta(hours=CACHE_HOURS):
        logger.info("cache hit %s", key)
        return json.loads(saved.payload)

    try:
        answer = fetch()
    except tmdb.TmdbError:
        if saved is None:
            raise
        logger.warning("TMDB unreachable, using the saved copy of %s", key)
        return json.loads(saved.payload)

    # Insert the answer, or replace the old copy if this key is already saved.
    payload = json.dumps(answer)
    db.execute(
        insert(TmdbCache)
        .values(cache_key=key, payload=payload, fetched_at=now)
        .on_conflict_do_update(
            index_elements=[TmdbCache.cache_key], set_={"payload": payload, "fetched_at": now}
        )
    )
    db.commit()
    return answer


def to_card(item: dict) -> dict:
    """One TMDB result, cut down to what a film card shows."""
    poster = item.get("poster_path")
    return {
        "tmdb_id": item["id"],
        "title": item.get("title") or "",
        "overview": item.get("overview") or "",
        "release_date": item.get("release_date") or None,
        "poster_url": f"{IMAGE_BASE}/{POSTER_SIZE}{poster}" if poster else None,
        "vote_average": item.get("vote_average"),
        "vote_count": item.get("vote_count"),
        "genre_ids": item.get("genre_ids", []),
    }


def cut_page(data: dict, page: int, per_page: int, offset: int) -> dict:
    """Our page of 10 or 20 films from one TMDB page, plus the pager numbers."""
    total = data["total_results"]
    last_page = TMDB_MAX_PAGE * TMDB_PAGE_SIZE // per_page  # TMDB stops at page 500
    return {
        "page": page,
        "per_page": per_page,
        "total_results": total,
        "total_pages": min(ceil(total / per_page), last_page),
        "results": [to_card(item) for item in data["results"][offset : offset + per_page]],
    }


def search(db: Session, query: str, page: int = 1, per_page: int = 10) -> dict:
    """Search films by title: our page of 10 or 20, cut from one cached TMDB page."""
    query = query.strip()
    tmdb_page, offset = to_tmdb_page(page, per_page)
    data = get_or_fetch(
        db, cache_key("search", query, tmdb_page), lambda: tmdb.search(query, tmdb_page)
    )
    return cut_page(data, page, per_page, offset)


def discover_filters(
    genre_ids: list[int],
    year_from: int | None,
    year_to: int | None,
    sort: str,
    region: str | None,
    min_rating: float | None,
) -> dict:
    """Turn our filter names into TMDB discover parameters."""
    filters: dict = {"sort_by": SORTS[sort]}
    if genre_ids:
        # "|" means OR: action or sci-fi. A "," would mean AND and find almost nothing.
        filters["with_genres"] = "|".join(str(g) for g in sorted(set(genre_ids)))
    if year_from:
        filters["primary_release_date.gte"] = f"{year_from}-01-01"
    latest = date.today() if sort == "newest" else None  # else unreleased films come first
    if year_to:
        latest = min(latest or date.max, date(year_to, 12, 31))
    if latest:
        filters["primary_release_date.lte"] = latest.isoformat()
    if region:
        filters["with_origin_country"] = region.upper()  # country the film comes from
    if min_rating is not None:
        filters["vote_average.gte"] = min_rating
    if sort == "rating" or min_rating is not None:
        filters["vote_count.gte"] = MIN_VOTES
    return filters


def discover(
    db: Session,
    genre_ids: list[int] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    sort: str = "popularity",
    region: str | None = None,
    min_rating: float | None = None,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    """Browse films by filters: our page of 10 or 20, cut from one cached TMDB page."""
    filters = discover_filters(genre_ids or [], year_from, year_to, sort, region, min_rating)
    tmdb_page, offset = to_tmdb_page(page, per_page)
    key = cache_key("discover", urlencode(sorted(filters.items())), tmdb_page)
    data = get_or_fetch(db, key, lambda: tmdb.discover(filters, tmdb_page))
    return cut_page(data, page, per_page, offset)


def to_date(text: str | None) -> date | None:
    """TMDB's "2010-07-15" as a date; None when it is empty or not a date."""
    try:
        return date.fromisoformat(text) if text else None
    except ValueError:
        return None


def save_movie(db: Session, data: dict) -> None:
    """Insert or update a film and its genre links, so users can like it later."""
    db.merge(
        Movie(
            tmdb_id=data["id"],
            title=data.get("title") or "",
            overview=data.get("overview") or None,
            release_date=to_date(data.get("release_date")),
            poster_path=data.get("poster_path"),
            vote_average=data.get("vote_average"),
            vote_count=data.get("vote_count"),
            popularity=data.get("popularity"),
            fetched_at=datetime.now(UTC),
        )
    )
    for genre in data.get("genres", []):
        db.merge(Genre(id=genre["id"], name=genre["name"]))
        db.merge(MovieGenre(movie_id=data["id"], genre_id=genre["id"]))
    db.commit()


def movie_detail(db: Session, tmdb_id: int) -> dict:
    """One film's page with its cast. The film is also saved in `movies`."""
    data = get_or_fetch(db, cache_key("movie", tmdb_id), lambda: tmdb.movie_detail(tmdb_id))
    save_movie(db, data)
    genres = [{"id": g["id"], "name": g["name"]} for g in data.get("genres", [])]
    cast = data.get("credits", {}).get("cast", [])[:CAST_SIZE]
    return {
        **to_card({**data, "genre_ids": [g["id"] for g in genres]}),
        "runtime": data.get("runtime"),
        "tagline": data.get("tagline") or "",
        "genres": genres,
        "cast": [
            {
                "name": person["name"],
                "character": person.get("character") or "",
                "profile_url": (
                    f"{IMAGE_BASE}/{PROFILE_SIZE}{person['profile_path']}"
                    if person.get("profile_path")
                    else None
                ),
            }
            for person in cast
        ],
    }


def list_genres(db: Session) -> list[Genre]:
    """All genres, from our genres table. Filled from TMDB the first time."""
    genres = db.scalars(select(Genre).order_by(Genre.name)).all()
    if not genres:
        for item in tmdb.genres():
            db.merge(Genre(id=item["id"], name=item["name"]))
        db.commit()
        genres = db.scalars(select(Genre).order_by(Genre.name)).all()
    return list(genres)
