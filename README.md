---
title: SecureTask API
emoji: 🔒
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# SecureTask API

A compact, **production-shaped REST backend** built security-first — JWT auth,
per-object authorization (IDOR-safe), input validation, rate limiting, pagination,
tests, and auto-generated interactive docs.

> Portfolio demo by **Aldo Rizona** — backend / middleware engineer (PHP · Python · Node/TS).
> This is the same shape of backend I build for clients: designed → implemented → tested → documented.

**▶ Interactive API docs:** run it locally (see **Run locally** below) and open **`/docs`** for
Swagger — register a user, click **Authorize**, then create and list tasks. One-line Docker start
is in **Deploy**.

---

## Why it's worth a look (not another to-do app)

The interesting part isn't the CRUD — it's how access is controlled:

- **JWT auth** — `register` / `login` / `refresh`. Passwords hashed with **bcrypt**.
  Access vs refresh tokens are separated by a signed `type` claim, so a refresh
  token can't be replayed as an access token.
- **Per-object authorization (IDOR-safe)** — every task is scoped to its owner.
  Requesting a task you don't own returns **404, not 403**, so the API never
  reveals that another user's resource exists. There's an explicit cross-account
  test proving user B cannot read/modify/delete user A's task.
- **Input validation** — Pydantic models give clean, typed `422` errors.
- **Rate limiting** — `login` is throttled (5/min/IP) to blunt brute force; a
  sane global default protects the rest.
- **Uniform-timing login** — a dummy hash is verified even when the email doesn't
  exist, so response timing doesn't leak which emails are registered.
- **Pagination** — list endpoints are bounded (`limit`/`offset`, capped at 100).
- **12-factor config** — everything via env; nothing secret hard-coded for prod.

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | — | create account (email + password ≥ 8) |
| POST | `/auth/login` | — | OAuth2 password form → access + refresh (throttled) |
| POST | `/auth/refresh` | — | new tokens from a valid refresh token |
| GET | `/auth/me` | ✅ | current user |
| GET | `/tasks` | ✅ | list own tasks — `?status=&limit=&offset=` |
| POST | `/tasks` | ✅ | create |
| GET | `/tasks/{id}` | ✅ | own task or 404 |
| PATCH | `/tasks/{id}` | ✅ | partial update |
| DELETE | `/tasks/{id}` | ✅ | delete |
| GET | `/health` | — | liveness probe |

Full request/response schemas live in the OpenAPI docs at `/docs` and `/redoc`.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

## Test

```bash
pytest -q
```
Covers registration, login failure paths, token-type enforcement, task CRUD,
pagination/filtering, validation errors, and the cross-account (IDOR) guarantee.

## Deploy

- **Render (free):** push to GitHub → *New +* → *Blueprint* (uses `render.yaml`;
  `SECRET_KEY` is generated for you). Swap `DATABASE_URL` for managed Postgres in prod.
- **Docker:** `docker build -t secure-task-api . && docker run -p 8000:8000 secure-task-api`

## Stack

FastAPI · SQLAlchemy 2.0 · Pydantic v2 · PyJWT · bcrypt · slowapi · pytest.
SQLite by default; Postgres/MySQL by changing one env var (no code change).

## Notes for reviewers / clients

This repo is deliberately small but complete — the goal is to show *how* I build,
not to ship a product. For a real engagement I'd add Alembic migrations, refresh-token
rotation/blacklist, structured logging + request IDs, and CI. Happy to walk through
any decision. — Aldo

_Licensed MIT._
