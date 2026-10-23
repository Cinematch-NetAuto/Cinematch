"""Every setting CineMatch uses, read once from the environment.

This is the only file that calls os.getenv. Values come from the .env file in
the repository root (a copy of .env.example) or from real environment
variables. Real environment variables win: that is how Jenkins passes its
secrets in without a .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # <repo>/.env
load_dotenv(ENV_FILE)  # a missing file is fine: the defaults below are used

# --- Database ---------------------------------------------------------------
# Same user, password and name as docker-compose.yml (local development only).
# 127.0.0.1, not "localhost": on some Windows PCs "localhost" tries IPv6 first
# and each new connection waits about 20 seconds before falling back.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://cinematch:cinematch@127.0.0.1:5432/cinematch"
)

# --- TMDB -------------------------------------------------------------------
TMDB_API_TOKEN = os.getenv("TMDB_API_TOKEN", "")  # empty until you add yours to .env
TMDB_BASE = os.getenv("TMDB_BASE", "https://api.themoviedb.org/3")
IMAGE_BASE = os.getenv("IMAGE_BASE", "https://image.tmdb.org/t/p")

# --- Login tokens -----------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "")  # no default on purpose: tokens need a real secret
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "24"))

# --- App --------------------------------------------------------------------
CACHE_HOURS = int(os.getenv("CACHE_HOURS", "6"))  # how long a saved TMDB answer stays fresh
CORS_ORIGINS = [  # websites allowed to call our API, comma-separated in .env
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# --- Google sign-in (optional) ----------------------------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")  # empty: Google sign-in is off
