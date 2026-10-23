"""Database tables as Python classes (SQLAlchemy models).

One class per table in db/schema.sql, one attribute per column, with the
same names. schema.sql creates the tables; these classes only describe them,
so a change to a table means editing both files. Models hold no logic.
Hot file: tell the team before you edit it.

All 8 tables are here. The indexes live only in schema.sql.
"""

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """The parent of every model."""


class User(Base):
    """A person with an account. Only a bcrypt hash of the password is kept."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)  # SERIAL: the database numbers users
    email: Mapped[str] = mapped_column(Text, unique=True)  # always stored lowercased
    password_hash: Mapped[str | None] = mapped_column(Text)  # bcrypt; None = Google only
    google_id: Mapped[str | None] = mapped_column(Text, unique=True)  # Google's "sub" id
    display_name: Mapped[str] = mapped_column(Text)
    content_language: Mapped[str] = mapped_column(Text, server_default="en-US")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Genre(Base):
    """A TMDB genre, e.g. 28 = Action."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)  # TMDB's own genre id
    name: Mapped[str] = mapped_column(Text)


class Movie(Base):
    """A film saved from TMDB. fetched_at says how old the copy is."""

    __tablename__ = "movies"

    tmdb_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    overview: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None]
    poster_path: Mapped[str | None] = mapped_column(Text)  # None: the film has no poster
    # asdecimal=False: read as float, ready for the scoring maths
    vote_average: Mapped[float | None] = mapped_column(Numeric(4, 2, asdecimal=False))
    vote_count: Mapped[int | None]
    popularity: Mapped[float | None] = mapped_column(Numeric(10, 3, asdecimal=False))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MovieGenre(Base):
    """Which genres a film has: one row per (film, genre) pair."""

    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), primary_key=True
    )
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), primary_key=True)


class TmdbCache(Base):
    """A saved TMDB answer: the same request within CACHE_HOURS skips TMDB."""

    __tablename__ = "tmdb_cache"

    cache_key: Mapped[str] = mapped_column(Text, primary_key=True)  # "search:inception:1"
    payload: Mapped[str] = mapped_column(Text)  # TMDB's JSON answer, as text
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Rating(Base):
    """A like (+1) or a dislike (-1). One per user and film: rating again replaces it."""

    __tablename__ = "ratings"
    __table_args__ = (CheckConstraint("value IN (-1, 1)", name="ratings_value_check"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.tmdb_id"), primary_key=True
    )
    value: Mapped[int] = mapped_column(SmallInteger)  # +1 like, -1 dislike
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WatchHistory(Base):
    """One "I watched this" event. The same film can be watched more than once."""

    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("movies.tmdb_id"))
    watched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserPreferences(Base):
    """What a user picked: starter genres (the cold-start fix), years, country, minimum rating."""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_genres: Mapped[list[int]] = mapped_column(ARRAY(Integer), server_default="{}")
    year_from: Mapped[int | None]
    year_to: Mapped[int | None]
    preferred_region: Mapped[str | None] = mapped_column(Text)  # country code, e.g. "AU"
    min_vote_average: Mapped[float] = mapped_column(
        Numeric(4, 2, asdecimal=False), server_default="0"
    )
