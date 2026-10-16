"""Password hashing (login tokens are added in a later step).

bcrypt turns a password into a one-way hash: quick to check, practically
impossible to turn back into the password. Only the hash is ever stored.
"""

import bcrypt

BCRYPT_ROUNDS = 12  # cost factor: each +1 doubles the time to hash, and to guess
MAX_PASSWORD_BYTES = 72  # bcrypt only reads the first 72 bytes of a password


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
