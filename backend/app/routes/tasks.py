from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user, require_crm_module
from app.models import Lead, Task, User
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(require_crm_module)])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    lead_id: int | None = Query(default=None),
    assigned_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Task).filter(Task.tenant_id == current_user.tenant_id)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    if lead_id:
        q = q.filter(Task.lead_id == lead_id)
    if assigned_user_id:
        q = q.filter(Task.assigned_user_id == assigned_user_id)
    return q.order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Valida lead_id se informado
    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.id == payload.lead_id, Lead.tenant_id == current_user.tenant_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    task = Task(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == current_user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
