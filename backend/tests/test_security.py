"""Tests for password hashing."""

import pytest

from app.security import MAX_PASSWORD_BYTES, hash_password, verify_password


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
