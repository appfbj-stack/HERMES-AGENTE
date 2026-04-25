from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, User
from ..schemas.common import TaskIn, TaskOut
from ..core.deps import get_current_user


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Task)
        .filter(Task.tenant_id == user.tenant_id)
        .order_by(Task.created_at.desc())
        .all()
    )


@router.post("", response_model=TaskOut)
def create_task(
    payload: TaskIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = Task(tenant_id=user.tenant_id, user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.tenant_id == user.tenant_id)
        .first()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.tenant_id == user.tenant_id)
        .first()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    db.delete(task)
    db.commit()
    return {"ok": True}
