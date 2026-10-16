"""Account endpoints: sign up, log in, and "who am I".

Sign-up also saves the user's starter genres in user_preferences. A new user
has no likes yet, so these genres are what the recommender starts from.
"""

from functools import cache

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, Db
from app.models import User, UserPreferences
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserOut
from app.security import create_token, hash_password, verify_password
from app.services import movies as movie_service
from app.tmdb import TmdbError

router = APIRouter(prefix="/api", tags=["accounts"])

# The same words for a wrong email and a wrong password, so the answer never
# tells a stranger which emails have an account.
BAD_LOGIN = "Invalid email or password"


@cache
def _stand_in_hash() -> str:
    """A real bcrypt hash to check unknown emails against: both cases take as long."""
    return hash_password("stand-in password for unknown emails")


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Db):
    """Create an account with its starter genres. The email must not be in use."""
    if db.scalar(select(User.id).where(User.email == body.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    try:
        known = {genre.id for genre in movie_service.list_genres(db)}
    except TmdbError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Genre list unavailable") from error
    unknown = sorted(set(body.genre_ids) - known)
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown genre ids: {unknown}")
    try:
        password_hash = hash_password(body.password)
    except ValueError as error:  # over 72 bytes: letters like "é" count as 2
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    user = User(email=body.email, password_hash=password_hash, display_name=body.display_name)
    try:
        db.add(user)
        db.flush()  # the database gives the user an id
        db.add(UserPreferences(user_id=user.id, preferred_genres=body.genre_ids))
        db.commit()
    except IntegrityError as error:  # the same email was registered a moment ago
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from error
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Db):
    """Swap an email and password for a login token."""
    user = db.scalar(select(User).where(User.email == body.email))
    password_ok = verify_password(body.password, user.password_hash if user else _stand_in_hash())
    if user is None or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, BAD_LOGIN, headers={"WWW-Authenticate": "Bearer"}
        )
    return TokenResponse(access_token=create_token(user.id))


@router.get("/users/me", response_model=UserOut)
def me(user: CurrentUser):
    """The logged-in user. On /docs, click Authorize and paste a token first."""
    return user
