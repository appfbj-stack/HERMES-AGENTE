import schedule
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Callable, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SkillExecution, User

_scheduled_jobs = {}
_scheduler_running = False
_scheduler_thread = None


def get_utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def execute_routine(
    db: Session,
    user: User,
    routine_name: str,
    routine_func: Callable,
    input_data: Optional[str] = None,
) -> dict:
    execution = SkillExecution(
        tenant_id=user.tenant_id,
        skill_name=routine_name,
        status="running",
        input_data=input_data,
        started_at=get_utcnow(),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        result = await routine_func(input_data) if input_data else await routine_func()
        execution.status = "completed"
        execution.output_data = str(result)
        execution.completed_at = get_utcnow()
        db.commit()
        return {"success": True, "execution_id": execution.id, "result": result}
    except Exception as exc:
        execution.status = "failed"
        execution.error_message = str(exc)
        execution.completed_at = get_utcnow()
        db.commit()
        return {"success": False, "execution_id": execution.id, "error": str(exc)}


async def execute_routine_sync(
    db: Session,
    user: User,
    routine_name: str,
    routine_func: Callable,
    input_data: Optional[str] = None,
) -> dict:
    execution = SkillExecution(
        tenant_id=user.tenant_id,
        skill_name=routine_name,
        status="running",
        input_data=input_data,
        started_at=get_utcnow(),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    try:
        result = routine_func(input_data) if input_data else routine_func()
        execution.status = "completed"
        execution.output_data = str(result)
        execution.completed_at = get_utcnow()
        db.commit()
        return {"success": True, "execution_id": execution.id, "result": result}
    except Exception as exc:
        execution.status = "failed"
        execution.error_message = str(exc)
        execution.completed_at = get_utcnow()
        db.commit()
        return {"success": False, "execution_id": execution.id, "error": str(exc)}


def schedule_routine(
    routine_name: str,
    routine_func: Callable,
    interval: str,
    interval_value: int,
    db_factory: Optional[Callable] = None,
    user_id: Optional[int] = None,
) -> dict:
    global _scheduler_running

    def job_wrapper():
        try:
            if db_factory and user_id:
                db_gen = db_factory()
                db = next(db_gen)
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        result = routine_func()
                finally:
                    db.close()
            else:
                result = routine_func()
        except Exception as exc:
            print(f"[scheduler] Error in {routine_name}: {exc}")

    job_id = f"{routine_name}_{user_id or 'system'}"

    if interval == "seconds":
        schedule.every(interval_value).seconds.do(job_wrapper)
    elif interval == "minutes":
        schedule.every(interval_value).minutes.do(job_wrapper)
    elif interval == "hours":
        schedule.every(interval_value).hours.do(job_wrapper)
    elif interval == "days":
        schedule.every(interval_value).days.do(job_wrapper)
    else:
        return {"success": False, "error": f"Invalid interval: {interval}"}

    _scheduled_jobs[job_id] = {"interval": interval, "interval_value": interval_value, "func": routine_func}

    if not _scheduler_running:
        start_scheduler()

    return {"success": True, "job_id": job_id}


def cancel_routine(job_id: str) -> dict:
    if job_id not in _scheduled_jobs:
        return {"success": False, "error": "Job not found"}

    schedule.clear(job_id)
    del _scheduled_jobs[job_id]

    if not _scheduled_jobs and _scheduler_running:
        stop_scheduler()

    return {"success": True, "job_id": job_id}


def list_scheduled_routines() -> dict:
    return {"success": True, "jobs": list(_scheduled_jobs.keys())}


def run_scheduler():
    global _scheduler_running
    while _scheduler_running:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    global _scheduler_running, _scheduler_thread
    if not _scheduler_running:
        _scheduler_running = True
        _scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        _scheduler_thread.start()


def stop_scheduler():
    global _scheduler_running
    _scheduler_running = False
