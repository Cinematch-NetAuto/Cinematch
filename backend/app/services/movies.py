"""Movie search logic: paging, caching and TMDB lookups.

For now this file holds only the paging maths. The cache and the search
functions are added in later steps.
"""

TMDB_PAGE_SIZE = 20  # TMDB always returns exactly 20 results per page
TMDB_MAX_PAGE = 500  # TMDB refuses any page number above 500


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
