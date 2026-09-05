"""SecureTask API — application entrypoint.

Run locally:  uvicorn app.main:app --reload
Interactive docs:  http://localhost:8000/docs  (Swagger)  ·  /redoc
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from . import __version__
from .config import get_settings
from .database import init_db
from .ratelimit import limiter
from .routers import auth, tasks

settings = get_settings()

DESCRIPTION = """
A compact, **security-first** REST backend built as a portfolio demo.

* **JWT auth** — register / login / refresh, bcrypt-hashed passwords
* **Per-object authorization** — you can only ever touch your own tasks (IDOR-safe: 404, never leaks existence)
* **Input validation** — Pydantic models, clear 422s
* **Rate limiting** — login throttled against brute force
* **Pagination** on list endpoints
* **Tested** — pytest suite incl. an explicit cross-account (IDOR) test

Try it: register, log in with **Authorize**, then create and list tasks.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=DESCRIPTION,
    contact={"name": "Aldo Rizona", "url": "https://github.com/aldorizona10-glitch"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
origins = ["*"] if settings.cors_origins.strip() == "*" else [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/", tags=["meta"])
def root():
    return {"name": settings.app_name, "version": __version__, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
