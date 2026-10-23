"""Account endpoints: sign up, log in (with a password or with Google), and "who am I".

Sign-up also saves the user's starter genres in user_preferences. A new user
has no likes yet, so these genres are what the recommender starts from.
"""

from functools import cache

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.config import GOOGLE_CLIENT_ID
from app.deps import CurrentUser, Db
from app.models import User, UserPreferences
from app.schemas import GoogleConfig, GoogleLogin, LoginRequest, TokenResponse, UserCreate, UserOut
from app.security import (
    GoogleUnreachable,
    InvalidGoogleToken,
    create_token,
    hash_password,
    verify_google_token,
    verify_password,
)
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
    # A Google-only account has no password: check the stand-in so it takes as long.
    has_password = user is not None and user.password_hash is not None
    password_ok = verify_password(
        body.password, user.password_hash if has_password else _stand_in_hash()
    )
    if not has_password or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, BAD_LOGIN, headers={"WWW-Authenticate": "Bearer"}
        )
    return TokenResponse(access_token=create_token(user.id))


@router.get("/users/me", response_model=UserOut)
def me(user: CurrentUser):
    """The logged-in user. On /docs, click Authorize and paste a token first."""
    return user


@router.get("/auth/google", response_model=GoogleConfig)
def google_config():
    """The client ID for the "Sign in with Google" button. Empty: Google sign-in is off."""
    return GoogleConfig(client_id=GOOGLE_CLIENT_ID)


@router.post("/auth/google", response_model=TokenResponse)
def google_sso(body: GoogleLogin, db: Db):
    """Log in or sign up with Google, and answer with our own login token.

    - Google's id is already saved: log that user in.
    - The email already has an email-and-password account: link Google to it, but
      only when Google says the email is verified and no other Google account is
      linked. Otherwise anyone could take that account over.
    - Otherwise: a new account with no password. Like sign-up, it needs 3 or more
      starter genres; without them the answer is 428, so the page can ask for them.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Google sign-in is not set up")
    try:
        idinfo = verify_google_token(body.credential)
    except GoogleUnreachable as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Google cannot be reached") from error
    except InvalidGoogleToken as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token") from error

    email = (idinfo.get("email") or "").lower()  # emails are always stored lowercased
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Google did not share an email address")
    google_id = idinfo["sub"]

    user = db.scalar(select(User).where(User.google_id == google_id))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            if user.google_id is not None or not idinfo.get("email_verified"):
                raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
            user.google_id = google_id  # link Google to the existing account
            db.commit()
    if user is not None:
        return TokenResponse(access_token=create_token(user.id))

    # --- New user: like sign-up, starter genres are needed and checked ---
    genre_ids = body.genre_ids
    if not genre_ids:  # the page then asks for genres and sends the same token again
        raise HTTPException(
            status.HTTP_428_PRECONDITION_REQUIRED, "Pick at least 3 genres to finish signing up"
        )
    try:
        known = {genre.id for genre in movie_service.list_genres(db)}
    except TmdbError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Genre list unavailable") from error
    unknown = sorted(set(genre_ids) - known)
    if unknown:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown genre ids: {unknown}")

    display_name = (idinfo.get("name") or email.split("@")[0])[:50]  # sign-up allows 50
    new_user = User(email=email, display_name=display_name, google_id=google_id)
    try:
        db.add(new_user)
        db.flush()  # the database gives the user an id
        db.add(UserPreferences(user_id=new_user.id, preferred_genres=genre_ids))
        db.commit()
    except IntegrityError as error:  # the same account was made a moment ago
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from error
    return TokenResponse(access_token=create_token(new_user.id))
