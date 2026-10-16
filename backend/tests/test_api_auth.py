"""API tests for accounts: register, log in, and the routes that need a login.

They use the shared fixtures in conftest.py: the test database and a fake TMDB.
"""

from app.models import UserPreferences

ACCOUNT = {
    "email": "sam@example.com",
    "password": "a long enough password",
    "display_name": "Sam",
    "genre_ids": [28, 18, 878],
}


def register(client, **changes):
    return client.post("/api/auth/register", json={**ACCOUNT, **changes})


def login(client, email=ACCOUNT["email"], password=ACCOUNT["password"]):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_login_and_me(client):
    assert register(client).status_code == 201
    token = login(client).json()["access_token"]

    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "sam@example.com"

    assert client.get("/api/users/me").status_code == 401  # the same call without a token


def test_register_never_returns_the_password(client):
    answer = register(client)
    assert "password" not in answer.text


def test_register_saves_the_starter_genres(client, db):
    user_id = register(client, genre_ids=[878, 28, 28, 18]).json()["id"]
    assert db.get(UserPreferences, user_id).preferred_genres == [18, 28, 878]


def test_duplicate_email_is_refused(client):
    register(client)
    answer = register(client, email="SAM@example.com")  # same email, other case
    assert answer.status_code == 409


def test_fewer_than_three_genres_is_refused(client):
    assert register(client, genre_ids=[28, 18]).status_code == 422
    assert register(client, genre_ids=[28, 28, 28]).status_code == 422


def test_unknown_genre_is_refused(client):
    assert register(client, genre_ids=[28, 18, 99999]).status_code == 422


def test_wrong_password_and_unknown_email_get_the_same_answer(client):
    register(client)
    wrong_password = login(client, password="not the password")
    unknown_email = login(client, email="nobody@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "Invalid email or password"}


def test_login_ignores_email_case_and_spaces(client):
    register(client)
    assert login(client, email="  Sam@Example.COM ").status_code == 200


def test_bad_token_is_refused(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/api/users/me", headers=headers).status_code == 401
