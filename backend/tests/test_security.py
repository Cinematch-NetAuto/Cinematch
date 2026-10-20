"""Tests for password hashing and login tokens."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app import security
from app.security import (
    MAX_PASSWORD_BYTES,
    InvalidToken,
    create_token,
    hash_password,
    read_token,
    verify_password,
)

TEST_SECRET = "test-secret-for-the-token-tests-only-" + "x" * 16


@pytest.fixture
def secret(monkeypatch):
    """Give the token functions a long test secret (no .env needed)."""
    monkeypatch.setattr(security, "JWT_SECRET", TEST_SECRET)


def test_right_password_passes():
    stored = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", stored)


def test_wrong_password_fails():
    stored = hash_password("correct horse battery staple")
    assert not verify_password("Correct horse battery staple", stored)


def test_same_password_hashed_twice_gives_two_different_hashes():
    # A random salt is mixed in, so equal passwords never look equal in the database.
    assert hash_password("same password") != hash_password("same password")


def test_hash_does_not_contain_the_password():
    stored = hash_password("my secret words")
    assert "my secret words" not in stored
    assert stored.startswith("$2b$12$")  # bcrypt, cost factor 12


def test_72_bytes_is_accepted():
    password = "a" * MAX_PASSWORD_BYTES
    assert verify_password(password, hash_password(password))


def test_over_72_bytes_is_rejected():
    with pytest.raises(ValueError):
        hash_password("a" * (MAX_PASSWORD_BYTES + 1))


def test_length_is_counted_in_bytes_not_characters():
    # "é" is 2 bytes in UTF-8, so 37 of them make 74 bytes: too long.
    with pytest.raises(ValueError):
        hash_password("é" * 37)


def test_overlong_password_never_verifies():
    stored = hash_password("a" * MAX_PASSWORD_BYTES)
    # Without the length check, bcrypt would ignore the extra "b" and say yes.
    assert not verify_password("a" * MAX_PASSWORD_BYTES + "b", stored)


# --- Login tokens ------------------------------------------------------------


@pytest.mark.usefixtures("secret")
def test_token_gives_back_the_user_id():
    assert read_token(create_token(42)) == 42


@pytest.mark.usefixtures("secret")
def test_changed_user_id_fails():
    # Anyone can read the payload, so swap user 1 for user 2 but keep the old signature.
    header, _, signature = create_token(1).split(".")
    claims = jwt.decode(create_token(1), options={"verify_signature": False})
    forged_payload = jwt.encode({**claims, "sub": "2"}, "any-other-key-" + "y" * 32).split(".")[1]
    with pytest.raises(InvalidToken):
        read_token(f"{header}.{forged_payload}.{signature}")


@pytest.mark.usefixtures("secret")
def test_token_signed_with_another_secret_fails():
    forged = jwt.encode({"sub": "1", "exp": 4102444800}, "a-different-secret-" + "z" * 32)
    with pytest.raises(InvalidToken):
        read_token(forged)


@pytest.mark.usefixtures("secret")
def test_expired_token_fails(monkeypatch):
    monkeypatch.setattr(security, "TOKEN_HOURS", -1)  # made already one hour out of date
    token = create_token(1)
    with pytest.raises(InvalidToken):
        read_token(token)


def token_issued_in(seconds: int) -> str:
    """A valid token whose "issued at" time is this many seconds from now."""
    issued = datetime.now(UTC) + timedelta(seconds=seconds)
    claims = {"sub": "1", "iat": issued, "exp": issued + timedelta(hours=1)}
    return jwt.encode(claims, TEST_SECRET, algorithm="HS256")


@pytest.mark.usefixtures("secret")
def test_token_survives_a_small_clock_step_back():
    # Inside Docker on Windows the clock was seen stepping back 3.8 s. A token made
    # just before such a step looks issued a few seconds in the future. Without
    # leeway it was refused, and about 1 test run in 30 failed with a 401.
    assert read_token(token_issued_in(5)) == 1


@pytest.mark.usefixtures("secret")
def test_token_issued_far_in_the_future_fails():
    with pytest.raises(InvalidToken):
        read_token(token_issued_in(300))


@pytest.mark.usefixtures("secret")
def test_unsigned_token_fails():
    # alg "none" means "no signature needed"; only HS256 is accepted.
    unsigned = jwt.encode({"sub": "1", "exp": 4102444800}, "", algorithm="none")
    with pytest.raises(InvalidToken):
        read_token(unsigned)


@pytest.mark.usefixtures("secret")
@pytest.mark.parametrize("token", ["", "not-a-token", "a.b.c"])
def test_garbage_fails(token):
    with pytest.raises(InvalidToken):
        read_token(token)


@pytest.mark.usefixtures("secret")
def test_token_without_expiry_fails():
    forever = jwt.encode({"sub": "1"}, TEST_SECRET, algorithm="HS256")
    with pytest.raises(InvalidToken):
        read_token(forever)


@pytest.mark.parametrize("bad_secret", ["", "too-short"])
def test_empty_or_short_secret_is_refused(monkeypatch, bad_secret):
    monkeypatch.setattr(security, "JWT_SECRET", bad_secret)
    with pytest.raises(RuntimeError):
        create_token(1)
    with pytest.raises(RuntimeError):
        read_token("anything")
