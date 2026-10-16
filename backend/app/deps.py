"""Shared FastAPI dependencies: a database session and the logged-in user.

Put `user: CurrentUser` on any route that needs a login. FastAPI then reads
the Authorization header, checks the token and loads the user before the
route runs. Anything wrong answers 401, and the route never runs.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import InvalidToken, read_token

# auto_error=False: a missing header gets our 401, not FastAPI's default 403.
bearer = HTTPBearer(auto_error=False, description="The access_token from /api/auth/login")

Db = Annotated[Session, Depends(get_db)]


def _unauthorized(detail: str) -> HTTPException:
    """A 401 answer that tells the client to log in with a Bearer token."""
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    """The user named in the request's Bearer token, or a 401."""
    if credentials is None:
        raise _unauthorized("Not logged in")
    try:
        user_id = read_token(credentials.credentials)
    except InvalidToken as error:
        raise _unauthorized("Invalid or expired token") from error
    user = db.get(User, user_id)
    if user is None:  # the account was deleted after the token was made
        raise _unauthorized("User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
