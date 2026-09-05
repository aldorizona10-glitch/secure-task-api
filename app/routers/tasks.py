"""Task CRUD. Every route requires auth and is scoped to the caller's own rows.

Authorization model: a task is only ever addressable by its owner. Requests for a
task the caller doesn't own return 404 (not 403) so the API never reveals whether
another user's resource exists — this is the IDOR-safe pattern.
"""
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from ..deps import DbDep, CurrentUser
from ..models import Task, TaskStatus
from ..schemas import TaskCreate, TaskUpdate, TaskOut, Page

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_owned_task_or_404(db, task_id: int, owner_id: int) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == owner_id))
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.get("", response_model=Page)
def list_tasks(
    db: DbDep,
    current: CurrentUser,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    base = select(Task).where(Task.owner_id == current.id)
    if status_filter is not None:
        base = base.where(Task.status == status_filter)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(base.order_by(Task.id.desc()).limit(limit).offset(offset)).all()
    return Page(items=rows, total=total or 0, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: DbDep, current: CurrentUser):
    task = Task(owner_id=current.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: DbDep, current: CurrentUser):
    return get_owned_task_or_404(db, task_id, current.id)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: DbDep, current: CurrentUser):
    task = get_owned_task_or_404(db, task_id, current.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: DbDep, current: CurrentUser):
    task = get_owned_task_or_404(db, task_id, current.id)
    db.delete(task)
    db.commit()
