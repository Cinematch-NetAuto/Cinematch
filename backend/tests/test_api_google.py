"""API tests for "Sign in with Google": POST /api/auth/google.

Google itself is never called: verify_google_token is replaced by a fake that
returns what Google would say about one person.
"""

import pytest

from app.models import User, UserPreferences
from app.routers import auth
from app.security import InvalidGoogleToken

PERSON = {"sub": "google-123", "email": "Gina@Example.com", "email_verified": True, "name": "Gina"}
ACCOUNT = {
    "email": "gina@example.com",
    "password": "a long enough password",
    "display_name": "Gina",
    "genre_ids": [28, 18, 878],
}


@pytest.fixture
def google(monkeypatch):
    """Switch Google sign-in on, with a fake Google. Change the returned dict to change it."""
    claims = dict(PERSON)
    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth, "verify_google_token", lambda token: dict(claims))
    return claims


def sign_in(client, **extra):
    return client.post("/api/auth/google", json={"credential": "a-google-id-token", **extra})


def test_first_sign_in_makes_an_account_with_no_password(client, db, google):
    answer = sign_in(client)
    assert answer.status_code == 200
    token = answer.json()["access_token"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["email"] == "gina@example.com"  # lowercased
    assert me["display_name"] == "Gina"
    user = db.query(User).one()
    assert user.password_hash is None
    assert user.google_id == "google-123"
    assert db.get(UserPreferences, user.id).preferred_genres == []


def test_starter_genres_are_saved_when_sent(client, db, google):
    assert sign_in(client, genre_ids=[878, 28, 18]).status_code == 200
    user = db.query(User).one()
    assert db.get(UserPreferences, user.id).preferred_genres == [18, 28, 878]


def test_unknown_genres_are_refused(client, google):
    assert sign_in(client, genre_ids=[1, 2, 3]).status_code == 422


def test_a_second_sign_in_is_the_same_account(client, db, google):
    sign_in(client)
    assert sign_in(client).status_code == 200
    assert db.query(User).count() == 1


def test_password_login_on_a_google_only_account_is_refused(client, google):
    sign_in(client)
    answer = client.post(
        "/api/auth/login", json={"email": "gina@example.com", "password": "any password"}
    )
    assert answer.status_code == 401


def test_a_verified_email_links_to_the_existing_account(client, db, google):
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    assert sign_in(client).status_code == 200
    assert db.query(User).one().google_id == "google-123"
    login = {"email": ACCOUNT["email"], "password": ACCOUNT["password"]}
    assert client.post("/api/auth/login", json=login).status_code == 200  # password still works


def test_an_unverified_email_is_not_linked(client, db, google):
    client.post("/api/auth/register", json=ACCOUNT)
    google["email_verified"] = False
    assert sign_in(client).status_code == 409
    assert db.query(User).one().google_id is None


def test_another_google_account_cannot_take_a_linked_email(client, db, google):
    sign_in(client)
    google["sub"] = "google-999"
    assert sign_in(client).status_code == 409


def test_a_bad_google_token_is_refused(client, monkeypatch):
    def refuse(token):
        raise InvalidGoogleToken("bad signature")

    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth, "verify_google_token", refuse)
    assert sign_in(client).status_code == 401


def test_google_sign_in_is_off_without_a_client_id(client, monkeypatch):
    monkeypatch.setattr(auth, "GOOGLE_CLIENT_ID", "")
    assert sign_in(client).status_code == 503
