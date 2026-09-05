"""Pydantic request/response models. These give automatic input validation
(clear 422 errors) and drive the OpenAPI docs."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from .models import TaskStatus


# ---- auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, examples=["hunter2-strong-pass"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---- tasks ----
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class Page(BaseModel):
    """Cursor-free, bounded pagination envelope for list endpoints."""
    items: list[TaskOut]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    detail: str
