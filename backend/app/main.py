"""CineMatch API: creates the FastAPI app.

Run from backend/:  uvicorn app.main:app --reload
Every endpoint is listed at http://localhost:8000/docs

Routers are added here one at a time, in the step that gives each one its
first endpoint. Hot file: tell the team before you edit it.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.schemas import HealthOut

app = FastAPI(title="CineMatch API", version="0.1.0")

# In development the Vite proxy makes the frontend and the API one address,
# so CORS never comes up. This only matters when a page on another address
# calls the API directly: only the origins in CORS_ORIGINS are let through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", response_model=HealthOut, tags=["health"])
def health() -> HealthOut:
    """Say the API is up: the first thing to check after starting it."""
    return HealthOut(status="ok")
