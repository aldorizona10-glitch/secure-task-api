from tests.conftest import make_user


def test_register_and_me(client):
    u = make_user(client, "alice@example.com")
    r = client.get("/auth/me", headers=u["headers"])
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_duplicate_email_conflicts(client):
    make_user(client, "dup@example.com")
    r = client.post("/auth/register", json={"email": "dup@example.com", "password": "supersecret123"})
    assert r.status_code == 409


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "x@example.com", "password": "short"})
    assert r.status_code == 422  # validation


def test_login_wrong_password(client):
    make_user(client, "bob@example.com")
    r = client.post("/auth/login", data={"username": "bob@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_refresh_issues_new_access(client):
    u = make_user(client, "carol@example.com")
    r = client.post("/auth/refresh", json={"refresh_token": u["refresh"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_access_token_cannot_be_used_as_refresh(client):
    u = make_user(client, "dave@example.com")
    access = u["headers"]["Authorization"].split()[1]
    r = client.post("/auth/refresh", json={"refresh_token": access})
    assert r.status_code == 401  # type claim mismatch rejected
