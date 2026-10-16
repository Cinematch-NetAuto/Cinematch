"""The only door to TMDB: every call to the movie database goes through here.

Nothing else in the project imports `requests`. That keeps the API token in
one place, gives every call a timeout and retries, and lets tests replace
these four functions with fakes, so the test suite needs no internet.

Every function returns TMDB's JSON as it comes (dicts and lists). Turning it
into our own shapes is the services' job.
"""

import logging
import time

import requests

from app.config import TMDB_API_TOKEN, TMDB_BASE

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10  # never wait longer than this for one answer
ATTEMPTS = 3  # the first try plus two retries
RETRY_WAIT_SECONDS = 1  # wait 1 s, then 2 s, before trying again
RETRY_STATUSES = {429, 500, 502, 503, 504}  # "busy, try again later" answers


class TmdbError(Exception):
    """TMDB could not be reached, or refused the request."""


class TmdbNotFound(TmdbError):
    """TMDB has nothing under that id (404)."""


def _get(path: str, params: dict | None = None) -> dict:
    """GET one TMDB endpoint and return its JSON, retrying short hiccups."""
    if not TMDB_API_TOKEN:
        raise TmdbError("TMDB_API_TOKEN is empty: put your token in .env")
    headers = {"Authorization": f"Bearer {TMDB_API_TOKEN}", "Accept": "application/json"}

    for attempt in range(1, ATTEMPTS + 1):
        logger.info("TMDB GET %s %s (attempt %d)", path, params or {}, attempt)
        try:
            response = requests.get(
                TMDB_BASE + path, params=params, headers=headers, timeout=TIMEOUT_SECONDS
            )
        except requests.RequestException as error:  # no answer: timeout, no network
            problem = f"no answer from TMDB ({type(error).__name__})"
        else:
            if response.status_code < 400:
                return response.json()
            problem = f"TMDB answered {response.status_code}"
            if response.status_code == 404:
                raise TmdbNotFound(problem)
            if response.status_code not in RETRY_STATUSES:
                raise TmdbError(problem)  # e.g. 401 bad token: retrying will not help
        if attempt < ATTEMPTS:
            time.sleep(RETRY_WAIT_SECONDS * attempt)

    raise TmdbError(f"{problem} after {ATTEMPTS} attempts")


def search(query: str, page: int = 1) -> dict:
    """Search films by title. One TMDB page: up to 20 results."""
    return _get("/search/movie", {"query": query, "page": page, "include_adult": "false"})


def discover(filters: dict, page: int = 1) -> dict:
    """Browse films by filters, given as TMDB parameter names.

    Example: {"with_genres": "28|878", "sort_by": "popularity.desc"}
    (a "|" between genres means OR; a "," would mean AND).
    """
    return _get("/discover/movie", {**filters, "page": page, "include_adult": "false"})


def movie_detail(tmdb_id: int) -> dict:
    """One film's details, with its cast in the same call."""
    return _get(f"/movie/{int(tmdb_id)}", {"append_to_response": "credits"})


def genres() -> list[dict]:
    """TMDB's movie genres: [{"id": 28, "name": "Action"}, ...]."""
    return _get("/genre/movie/list")["genres"]
