"""Database tables as Python classes (SQLAlchemy models).

One class per table in db/schema.sql, one attribute per column, with the
same names. schema.sql creates the tables; these classes only describe them,
so a change to a table means editing both files. Models hold no logic.
Hot file: tell the team before you edit it.

Ratings, watch history and preferences are added in the next step.
"""

from datetime import date, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """The parent of every model."""


class User(Base):
    """A person with an account. Only a bcrypt hash of the password is kept."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)  # SERIAL: the database numbers users
    email: Mapped[str] = mapped_column(Text, unique=True)  # always stored lowercased
    password_hash: Mapped[str] = mapped_column(Text)  # bcrypt output, never the password
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
