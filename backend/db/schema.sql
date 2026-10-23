-- CineMatch database: 8 tables.
-- Run with:  python -m scripts.init_db   (from backend/)
-- Safe to run more than once: every statement checks first or changes nothing twice.
-- Read top to bottom: tables that others point at come first.

-- People with accounts.
CREATE TABLE IF NOT EXISTS users (
    id               SERIAL PRIMARY KEY,
    email            TEXT NOT NULL UNIQUE,          -- always stored lowercased
    password_hash    TEXT,                          -- bcrypt output; empty for Google-only accounts
    google_id        TEXT UNIQUE,                   -- Google's fixed id for this person, if linked
    display_name     TEXT NOT NULL,
    content_language TEXT NOT NULL DEFAULT 'en-US', -- language for titles and overviews
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Google sign-in came later. These two lines bring an older database up to date;
-- on a new database they change nothing.
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE;

-- TMDB's genre list, copied once at setup. The ids are TMDB's, not ours.
CREATE TABLE IF NOT EXISTS genres (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- Our local copy of films we have fetched. This is a cache, not the source of
-- truth: TMDB owns the data, and fetched_at says how old our copy is.
CREATE TABLE IF NOT EXISTS movies (
    tmdb_id      BIGINT PRIMARY KEY,
    title        TEXT NOT NULL,
    overview     TEXT,
    release_date DATE,
    poster_path  TEXT,                              -- may be NULL: not every film has a poster
    vote_average NUMERIC(4,2),
    vote_count   INTEGER,
    popularity   NUMERIC(10,3),
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Which genres each film has. A film has many genres and a genre has many
-- films, so the pairs need their own table (a many-to-many relationship).
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id BIGINT  NOT NULL REFERENCES movies(tmdb_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id),
    PRIMARY KEY (movie_id, genre_id)
);

-- Likes and dislikes. One opinion per user per film, so (user, film) is the key.
CREATE TABLE IF NOT EXISTS ratings (
    user_id    INTEGER  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   BIGINT   NOT NULL REFERENCES movies(tmdb_id),
    value      SMALLINT NOT NULL CHECK (value IN (-1, 1)),   -- +1 like, -1 dislike
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, movie_id)
);

-- Films the user has watched. No unique key, because you can watch a film again.
CREATE TABLE IF NOT EXISTS watch_history (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   BIGINT  NOT NULL REFERENCES movies(tmdb_id),
    watched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- What the user told us they like. One row per user.
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id          INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferred_genres INTEGER[] NOT NULL DEFAULT '{}',   -- e.g. {28, 878}
    year_from        INTEGER,
    year_to          INTEGER,
    preferred_region TEXT,                              -- ISO country code, e.g. 'AU'
    min_vote_average NUMERIC(4,2) NOT NULL DEFAULT 0
);

-- Saved TMDB answers, so we never ask TMDB the same question twice.
CREATE TABLE IF NOT EXISTS tmdb_cache (
    cache_key  TEXT PRIMARY KEY,                    -- e.g. 'search:inception:1'
    payload    TEXT NOT NULL,                       -- the raw JSON answer, as text
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes: make the queries we actually run fast.
CREATE INDEX IF NOT EXISTS ix_ratings_user ON ratings (user_id);
CREATE INDEX IF NOT EXISTS ix_history_user ON watch_history (user_id, watched_at DESC);
CREATE INDEX IF NOT EXISTS ix_mg_genre     ON movie_genres (genre_id);
