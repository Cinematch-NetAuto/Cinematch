"""Password hashing and login tokens.

bcrypt turns a password into a one-way hash: quick to check, practically
impossible to turn back into the password. Only the hash is ever stored.

A login token (JWT) is a signed note that says "this is user N, until time T".
Anyone can read it, but only the server, which knows JWT_SECRET, can make one
that passes read_token(). This is the only file that uses the jwt library.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET, TOKEN_HOURS

BCRYPT_ROUNDS = 12  # cost factor: each +1 doubles the time to hash, and to guess
MAX_PASSWORD_BYTES = 72  # bcrypt only reads the first 72 bytes of a password
MIN_SECRET_LENGTH = 32  # a shorter secret can be guessed offline from one token
# Clocks get corrected: inside Docker on Windows one stepped back 3.8 s. Without
# leeway, a token made just before such a step looks "issued in the future" and is
# refused, so a freshly logged-in user gets a 401. 30 s covers that and stays tiny
# next to the token's lifetime of TOKEN_HOURS.
CLOCK_LEEWAY = timedelta(seconds=30)


class InvalidToken(Exception):
    """The token is tampered with, expired, signed with another secret, or not a token."""


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the password, safe to store in the database.

    Raises ValueError for passwords longer than 72 bytes: bcrypt would silently
    ignore everything after byte 72, so two different passwords could match.
    """
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValueError(f"password is longer than {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """True if the password matches the stored hash."""
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        return False  # such a password could never have been stored
    return bcrypt.checkpw(raw, password_hash.encode("ascii"))


def _secret() -> str:
    """The signing secret. With an empty or short one, anyone could forge tokens."""
    if len(JWT_SECRET) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be at least {MIN_SECRET_LENGTH} characters: set it in .env"
        )
    return JWT_SECRET


def create_token(user_id: int) -> str:
    """Make a signed token that says "this is user N", valid for TOKEN_HOURS."""
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(hours=TOKEN_HOURS)}
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def read_token(token: str) -> int:
    """Check the signature and the expiry, and return the user id.

    Raises InvalidToken for any bad token. Only JWT_ALGORITHM is accepted, so a
    token that claims "no signature needed" (alg "none") is refused too.
    """
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[JWT_ALGORITHM],
            leeway=CLOCK_LEEWAY,
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError) as error:
        raise InvalidToken(str(error)) from error
