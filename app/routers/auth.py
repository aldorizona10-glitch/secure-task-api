"""Authentication: register, login (throttled), refresh, and whoami."""
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from ..deps import DbDep, CurrentUser
from ..models import User
from ..ratelimit import limiter
from ..schemas import UserCreate, UserOut, Token, RefreshRequest
from ..security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbDep):
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _issue(user: User) -> Token:
    sub = str(user.id)
    return Token(access_token=create_access_token(sub), refresh_token=create_refresh_token(sub))


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # brute-force throttle; keyed by client IP
def login(request: Request, db: DbDep, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = db.scalar(select(User).where(User.email == form.username))
    # Verify even on missing user to keep timing uniform, then fail uniformly.
    ok = verify_password(form.password, user.hashed_password) if user else verify_password(form.password, "$2b$12$" + "x" * 53)
    if not user or not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return _issue(user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: DbDep):
    try:
        data = decode_token(payload.refresh_token, expected_type="refresh")
        user = db.get(User, int(data["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _issue(user)


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser):
    return current
