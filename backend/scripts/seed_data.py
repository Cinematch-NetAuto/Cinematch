"""Fill the database with demo data: 19 genres, 12 films and 3 demo users.

Run from backend/:  python -m scripts.seed_data

Safe to run again: genres and films are updated, and the three demo users are
deleted and made again from scratch. Other users are never touched. Works
offline: the film data below is a snapshot from TMDB, taken on 2026-10-16.

Demo logins (password "demo-password" for all three):
    ava@example.com   likes action and science fiction
    ben@example.com   likes drama and romance
    cleo@example.com  likes animation and family films
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import engine
from app.models import Genre, Movie, MovieGenre, Rating, User, UserPreferences, WatchHistory
from app.security import hash_password
from scripts.init_db import init_db

DEMO_PASSWORD = "demo-password"  # demo accounts only, never a real password

# TMDB's 19 movie genres: id -> name
GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}  # fmt: skip

# (tmdb_id, title, release date, genre ids, vote average, vote count, popularity)
FILMS = [
    (27205, "Inception", "2010-07-15", [28, 878, 80], 8.37, 40442, 61.4),
    (157336, "Interstellar", "2014-11-04", [12, 18, 878], 8.49, 41499, 77.0),
    (155, "The Dark Knight", "2008-07-16", [28, 53, 80], 8.54, 36975, 55.6),
    (603, "The Matrix", "1999-03-31", [28, 878], 8.26, 28966, 50.5),
    (13, "Forrest Gump", "1994-06-23", [35, 18, 10749], 8.46, 30666, 44.7),
    (278, "The Shawshank Redemption", "1994-09-23", [18, 80], 8.73, 31589, 54.1),
    (680, "Pulp Fiction", "1994-09-10", [53, 80, 35], 8.48, 31089, 53.9),
    (597, "Titanic", "1997-12-18", [18, 10749], 7.9, 27904, 57.5),
    (129, "Spirited Away", "2001-07-20", [16, 10751, 14], 8.54, 19050, 74.5),
    (862, "Toy Story", "1995-11-22", [10751, 35, 16, 12], 7.99, 20669, 43.6),
    (496243, "Parasite", "2019-05-30", [35, 53, 18], 8.49, 21489, 42.7),
    (419430, "Get Out", "2017-02-24", [9648, 53, 27], 7.63, 19485, 39.6),
]  # fmt: skip

# Poster file names on TMDB's image server, by tmdb_id
POSTERS = {
    27205: "/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg",
    157336: "/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg",
    155: "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    603: "/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg",
    13: "/saHP97rTPS5eLmrLQEcANmKrsFl.jpg",
    278: "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
    680: "/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg",
    597: "/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",
    129: "/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
    862: "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
    496243: "/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
    419430: "/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg",
}

LIKE, DISLIKE = 1, -1
DEMO_USERS = [
    {
        "email": "ava@example.com",
        "name": "Ava",
        "genres": [28, 53, 878],
        "ratings": {27205: LIKE, 603: LIKE, 155: LIKE, 597: DISLIKE},
        "watched": [27205, 157336],
    },
    {
        "email": "ben@example.com",
        "name": "Ben",
        "genres": [18, 35, 10749],
        "ratings": {13: LIKE, 278: LIKE, 597: LIKE, 419430: DISLIKE},
        "watched": [597],
    },
    {
        "email": "cleo@example.com",
        "name": "Cleo",
        "genres": [16, 35, 10751],
        "ratings": {129: LIKE, 862: LIKE, 680: DISLIKE},
        "watched": [862, 129],
    },
]


def count(db: Session, model) -> int:
    """How many rows a table has."""
    return db.scalar(select(func.count()).select_from(model))


def seed(db: Session) -> dict:
    """Write the demo data and return how many rows each table now holds."""
    for genre_id, name in GENRES.items():
        db.merge(Genre(id=genre_id, name=name))
    for tmdb_id, title, released, genre_ids, average, votes, popularity in FILMS:
        db.merge(
            Movie(
                tmdb_id=tmdb_id,
                title=title,
                release_date=date.fromisoformat(released),
                poster_path=POSTERS[tmdb_id],
                vote_average=average,
                vote_count=votes,
                popularity=popularity,
            )
        )
        for genre_id in genre_ids:  # a like points at a film, so films go in first
            db.merge(MovieGenre(movie_id=tmdb_id, genre_id=genre_id))
    db.flush()

    # Start the demo users from scratch: the cascade removes their old rows too.
    db.execute(delete(User).where(User.email.in_([demo["email"] for demo in DEMO_USERS])))
    now = datetime.now(UTC)
    for demo in DEMO_USERS:
        user = User(
            email=demo["email"],
            password_hash=hash_password(DEMO_PASSWORD),
            display_name=demo["name"],
        )
        db.add(user)
        db.flush()  # the database gives the user an id
        db.add(UserPreferences(user_id=user.id, preferred_genres=sorted(demo["genres"])))
        for movie_id, value in demo["ratings"].items():
            db.add(Rating(user_id=user.id, movie_id=movie_id, value=value))
        for days_ago, movie_id in enumerate(demo["watched"], start=1):
            watched_at = now - timedelta(days=days_ago)
            db.add(WatchHistory(user_id=user.id, movie_id=movie_id, watched_at=watched_at))
    db.commit()
    return {
        "genres": count(db, Genre),
        "films": count(db, Movie),
        "users": count(db, User),
        "ratings": count(db, Rating),
        "watched": count(db, WatchHistory),
    }


if __name__ == "__main__":
    init_db()
    with Session(engine) as session:
        totals = seed(session)
    print(
        f"Demo data ready: {totals['genres']} genres, {totals['films']} films, "
        f"{totals['users']} users, {totals['ratings']} ratings, {totals['watched']} watched."
    )
    print(f"Demo logins: ava@, ben@, cleo@example.com, password {DEMO_PASSWORD!r}")
