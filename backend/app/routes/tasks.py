from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Task, User
from app.schemas import TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.tenant_id == current_user.tenant_id).order_by(Task.created_at.desc()).all()


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = Task(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

