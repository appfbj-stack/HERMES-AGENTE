from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    CoolifyDeployRequest,
    CoolifyDeploymentsRequest,
    CoolifyStatusRequest,
    CoolifyTriggerRequest,
    FileDeleteRequest,
    FileListRequest,
    FileReadRequest,
    FileWriteRequest,
    GitHubCommitRequest,
    GitHubPullRequestRequest,
    GitHubPushRequest,
    RoutineCancelRequest,
    RoutineExecuteRequest,
    RoutineScheduleRequest,
    SkillExecutionOut,
    SkillExecutionsListOut,
    SocialFileDeleteRequest,
    SocialFileListRequest,
    SocialFileReadRequest,
    SocialFileWriteRequest,
)
from app.services.coolify import (
    coolify_deploy,
    coolify_get_deployments,
    coolify_get_status,
    coolify_trigger_webhook,
)
from app.services.file_reader import delete_file, list_files, read_file, write_file
from app.services.github import github_commit, github_create_pull_request, github_push
from app.services.scheduler import (
    cancel_routine,
    execute_routine,
    list_scheduled_routines,
    schedule_routine,
)
from app.services.social_reader import (
    delete_social_file,
    list_social_files,
    read_social_file,
    write_social_file,
)

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("/github/commit")
async def tools_github_commit(
    payload: GitHubCommitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await github_commit(db, current_user, payload.message, payload.files, payload.author_name, payload.author_email)


@router.post("/github/push")
async def tools_github_push(
    payload: GitHubPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await github_push(db, current_user, payload.branch)


@router.post("/github/pull-request")
async def tools_github_pull_request(
    payload: GitHubPullRequestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await github_create_pull_request(db, current_user, payload.title, payload.body, payload.head, payload.base)


@router.get("/files/list")
async def tools_list_files(
    path: str = "./",
    pattern: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_files(db, current_user, path, pattern)


@router.get("/files/read")
async def tools_read_file(
    path: str,
    encoding: str = "utf-8",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await read_file(db, current_user, path, encoding)


@router.post("/files/write")
async def tools_write_file(
    payload: FileWriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await write_file(db, current_user, payload.path, payload.content, payload.encoding, payload.create_dirs)


@router.post("/files/delete")
async def tools_delete_file(
    payload: FileDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delete_file(db, current_user, payload.path)


@router.post("/coolify/deploy")
async def tools_coolify_deploy(
    payload: CoolifyDeployRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await coolify_deploy(db, current_user, payload.application_id, payload.branch, payload.force_rebuild)


@router.post("/coolify/trigger")
async def tools_coolify_trigger(
    payload: CoolifyTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await coolify_trigger_webhook(db, current_user, payload.webhook_url, payload.payload)


@router.get("/coolify/status")
async def tools_coolify_status(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await coolify_get_status(db, current_user, application_id)


@router.get("/coolify/deployments")
async def tools_coolify_deployments(
    application_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await coolify_get_deployments(db, current_user, application_id, limit)


@router.get("/social/files")
async def tools_list_social_files(
    pattern: str | None = None,
    subfolder: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_social_files(db, current_user, pattern, subfolder)


@router.get("/social/files/read")
async def tools_read_social_file(
    filename: str,
    subfolder: str | None = None,
    encoding: str = "utf-8",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await read_social_file(db, current_user, filename, subfolder, encoding)


@router.post("/social/files/write")
async def tools_write_social_file(
    payload: SocialFileWriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await write_social_file(db, current_user, payload.filename, payload.content, payload.subfolder, payload.encoding)


@router.post("/social/files/delete")
async def tools_delete_social_file(
    payload: SocialFileDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await delete_social_file(db, current_user, payload.filename, payload.subfolder)


@router.post("/routines/execute")
async def tools_execute_routine(
    payload: RoutineExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import SkillExecution

    def sample_routine(input_data: str | None = None):
        return f"Routine executed with input: {input_data or 'no input'}"

    return await execute_routine(db, current_user, payload.routine_name, sample_routine, payload.input_data)


@router.post("/routines/schedule")
async def tools_schedule_routine(
    payload: RoutineScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def sample_routine():
        return f"Scheduled routine {payload.routine_name} executed"

    return schedule_routine(
        payload.routine_name,
        sample_routine,
        payload.interval,
        payload.interval_value,
        get_db,
        current_user.id,
    )


@router.post("/routines/cancel")
async def tools_cancel_routine(
    payload: RoutineCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_routine(payload.job_id)


@router.get("/routines/scheduled")
async def tools_list_scheduled_routines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_scheduled_routines()


@router.get("/executions", response_model=SkillExecutionsListOut)
async def tools_list_executions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import SkillExecution

    executions = (
        db.query(SkillExecution)
        .filter(SkillExecution.tenant_id == current_user.tenant_id)
        .order_by(SkillExecution.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    total = (
        db.query(SkillExecution)
        .filter(SkillExecution.tenant_id == current_user.tenant_id)
        .count()
    )

    return SkillExecutionsListOut(executions=executions, total=total)


@router.get("/executions/{execution_id}", response_model=SkillExecutionOut)
async def tools_get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models import SkillExecution

    execution = (
        db.query(SkillExecution)
        .filter(
            SkillExecution.id == execution_id,
            SkillExecution.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

    return execution
