"""Measure the recommender offline: does it find films a user liked?

Run from backend/:  python -m scripts.evaluate

Leave-one-out on the three demo users from scripts/seed_data.py: hide one of a
user's likes, ask the real recommender for that user's films, and check whether
the hidden film comes back in the top 10. Each like is hidden once, so the demo
users' 8 likes give 8 trials.

Precision@10 = hidden films found in the top 10, divided by 10, averaged over
the trials. With one hidden film per trial it is at most 0.10, so the script
also prints the hit count. It runs twice: with the real weights (taste 0.7,
quality 0.3) and with one change (taste 0.5, quality 0.5).

Each trial uses a temporary stand-in user: a copy of the demo user's genres,
likes, dislikes and watch history, without the hidden film. Each stand-in is
deleted right after its trial, and the real demo users are never changed. Needs
the demo films in the database (python -m scripts.seed_data), and TMDB or a
warm cache.
"""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import engine
from app.models import Rating, User, UserPreferences, WatchHistory
from app.security import hash_password
from app.services import recommend as recommend_service
from scripts.seed_data import DEMO_USERS, FILMS, LIKE

K = 10  # the "top 10" in Precision@10
STAND_IN_EMAIL = "evaluation-{n}@example.invalid"  # .invalid: never a real address
REAL_WEIGHTS = (0.7, 0.3)  # (taste, quality), as in services/recommend.py
CHANGED_WEIGHTS = (0.5, 0.5)  # the one weight change this evaluation tries
TITLES = {tmdb_id: title for tmdb_id, title, *_ in FILMS}


def trials() -> list[tuple[dict, int]]:
    """Every (demo user, hidden film) pair: each demo like is hidden once."""
    return [
        (demo, tmdb_id)
        for demo in DEMO_USERS
        for tmdb_id, value in demo["ratings"].items()
        if value == LIKE
    ]


def precision_at_k(recommended: list[int], relevant: set[int], k: int = K) -> float:
    """How many of the first k recommendations are relevant, divided by k."""
    return len(set(recommended[:k]) & relevant) / k


def add_stand_in(db: Session, n: int, demo: dict, hidden: int) -> int:
    """A temporary copy of a demo user who has never seen `hidden`. Returns its id."""
    user = User(
        email=STAND_IN_EMAIL.format(n=n),
        password_hash=hash_password(secrets.token_urlsafe(32)),  # nobody can log in
        display_name="Evaluation",
    )
    db.add(user)
    db.flush()  # the database gives the user an id
    db.add(UserPreferences(user_id=user.id, preferred_genres=sorted(demo["genres"])))
    for tmdb_id, value in demo["ratings"].items():
        if tmdb_id != hidden:
            db.add(Rating(user_id=user.id, movie_id=tmdb_id, value=value))
    now = datetime.now(UTC)
    for days_ago, tmdb_id in enumerate(demo["watched"], start=1):
        if tmdb_id != hidden:
            watched_at = now - timedelta(days=days_ago)
            db.add(WatchHistory(user_id=user.id, movie_id=tmdb_id, watched_at=watched_at))
    db.commit()
    return user.id


def remove_stand_ins(db: Session) -> None:
    """Delete every stand-in; the database deletes their likes and history too.

    The rollback first ends a transaction that an error left half-done, so the
    clean-up still works after a failed trial.
    """
    db.rollback()
    db.execute(delete(User).where(User.email.like(STAND_IN_EMAIL.format(n="%"))))
    db.commit()


def evaluate(db: Session, weights: tuple[float, float]) -> tuple[float, int, list[str]]:
    """Run every trial with these (taste, quality) weights.

    Returns the mean Precision@10, the number of hidden films found in the top
    10, and one line per trial.
    """
    recommend_service.TASTE_WEIGHT, recommend_service.QUALITY_WEIGHT = weights
    try:
        scores, hits, lines = [], 0, []
        for n, (demo, hidden) in enumerate(trials()):
            user_id = add_stand_in(db, n, demo, hidden)
            try:
                picks = recommend_service.recommend(db, user_id)
            finally:
                remove_stand_ins(db)  # one stand-in at a time, gone before the next
            ids = [pick["tmdb_id"] for pick in picks]
            scores.append(precision_at_k(ids, {hidden}))
            if hidden in ids[:K]:
                hits += 1
                found = f"found at rank {ids.index(hidden) + 1}"
            elif hidden in ids:
                found = f"not in the top {K} (rank {ids.index(hidden) + 1} of {len(ids)})"
            else:
                found = f"not in the top {K} (not among the {len(ids)} recommendations)"
            lines.append(f"  {demo['name']:4}  hidden {TITLES[hidden]}: {found}")
        return sum(scores) / len(scores), hits, lines
    finally:
        recommend_service.TASTE_WEIGHT, recommend_service.QUALITY_WEIGHT = REAL_WEIGHTS


def main() -> None:
    runs = (("Real weights", REAL_WEIGHTS), ("Changed weights", CHANGED_WEIGHTS))
    with Session(engine) as db:
        remove_stand_ins(db)  # leftovers from a run that was stopped half-way
        for label, weights in runs:
            precision, hits, lines = evaluate(db, weights)
            print(f"{label} (taste {weights[0]}, quality {weights[1]}):")
            print("\n".join(lines))
            print(f"  Hidden films found in the top {K}: {hits} of {len(lines)}")
            print(f"  Precision@{K}: {precision:.3f}\n")


if __name__ == "__main__":
    main()
