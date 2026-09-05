from tests.conftest import make_user


def test_requires_auth(client):
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"title": "x"}).status_code == 401


def test_create_get_update_delete(client):
    u = make_user(client, "owner@example.com")
    h = u["headers"]

    r = client.post("/tasks", json={"title": "Write proposal", "description": "for client"}, headers=h)
    assert r.status_code == 201
    tid = r.json()["id"]
    assert r.json()["status"] == "todo"

    assert client.get(f"/tasks/{tid}", headers=h).status_code == 200

    r = client.patch(f"/tasks/{tid}", json={"status": "done"}, headers=h)
    assert r.status_code == 200 and r.json()["status"] == "done"

    assert client.delete(f"/tasks/{tid}", headers=h).status_code == 204
    assert client.get(f"/tasks/{tid}", headers=h).status_code == 404


def test_list_pagination_and_filter(client):
    u = make_user(client, "lister@example.com")
    h = u["headers"]
    for i in range(25):
        client.post("/tasks", json={"title": f"t{i}", "status": "done" if i % 2 else "todo"}, headers=h)

    r = client.get("/tasks?limit=10&offset=0", headers=h)
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 25 and len(body["items"]) == 10

    r = client.get("/tasks?status=done", headers=h)
    assert all(t["status"] == "done" for t in r.json()["items"])


def test_idor_cross_account_returns_404(client):
    """The core authorization guarantee: user B cannot read/modify user A's task,
    and the API does not reveal that it exists (404, not 403)."""
    alice = make_user(client, "alice2@example.com")
    bob = make_user(client, "bob2@example.com")

    r = client.post("/tasks", json={"title": "alice private"}, headers=alice["headers"])
    alice_task = r.json()["id"]

    # Bob probing Alice's task id
    assert client.get(f"/tasks/{alice_task}", headers=bob["headers"]).status_code == 404
    assert client.patch(f"/tasks/{alice_task}", json={"title": "hijacked"}, headers=bob["headers"]).status_code == 404
    assert client.delete(f"/tasks/{alice_task}", headers=bob["headers"]).status_code == 404

    # Alice's task is untouched
    r = client.get(f"/tasks/{alice_task}", headers=alice["headers"])
    assert r.status_code == 200 and r.json()["title"] == "alice private"

    # Bob's own listing never includes Alice's rows
    assert client.get("/tasks", headers=bob["headers"]).json()["total"] == 0


def test_validation_error_on_empty_title(client):
    u = make_user(client, "val@example.com")
    r = client.post("/tasks", json={"title": ""}, headers=u["headers"])
    assert r.status_code == 422
