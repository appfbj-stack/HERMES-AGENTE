from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    AdminActionLogListOut,
    AdminActionLogOut,
    AdminMemoryCreate,
    AdminMemoryListOut,
    AdminMemoryOut,
    AdminMemoryUpdate,
    AdminProjectCreate,
    AdminProjectListOut,
    AdminProjectOut,
    AdminProjectUpdate,
    AdminRoutineCreate,
    AdminRoutineListOut,
    AdminRoutineOut,
    AdminRoutineUpdate,
    AdminSkillCreate,
    AdminSkillListOut,
    AdminSkillOut,
    AdminSkillRunRequest,
    AdminSkillRunResponse,
    AdminSkillUpdate,
    AdminTaskCreate,
    AdminTaskListOut,
    AdminTaskOut,
    AdminTaskUpdate,
    HermesAdminChatRequest,
    HermesAdminChatResponse,
    HermesAdminDashboardOut,
)
from app.services.hermes_admin import HermesAdminService


def _require_super_admin(user: User = Depends(get_current_user)) -> User:
    """Verifica se o usuário é super admin."""
    if not user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    return user


router = APIRouter(prefix="/admin/hermes", tags=["admin-hermes"])


@router.post("/chat", response_model=HermesAdminChatResponse)
async def hermes_chat(
    payload: HermesAdminChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Chat com Hermes Admin Master."""
    service = HermesAdminService(db)
    return await service.chat(user, payload.message)


@router.get("/dashboard", response_model=HermesAdminDashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Dashboard administrativo."""
    service = HermesAdminService(db)
    return service.get_dashboard()


@router.get("/tasks", response_model=AdminTaskListOut)
def get_tasks(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista tarefas administrativas."""
    service = HermesAdminService(db)
    tasks, total = service.get_tasks(status, limit, offset)
    return AdminTaskListOut(tasks=tasks, total=total)


@router.post("/tasks", response_model=AdminTaskOut)
def create_task(
    payload: AdminTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Cria tarefa administrativa."""
    service = HermesAdminService(db)
    return service.create_task(payload.model_dump(), user)


@router.patch("/tasks/{task_id}", response_model=AdminTaskOut)
def update_task(
    task_id: int,
    payload: AdminTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Atualiza tarefa administrativa."""
    service = HermesAdminService(db)
    task = service.update_task(task_id, payload.model_dump(exclude_unset=True), user)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Deleta tarefa administrativa."""
    from app.models import AdminTask

    task = db.query(AdminTask).filter(AdminTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()


@router.get("/projects", response_model=AdminProjectListOut)
def get_projects(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista projetos administrativos."""
    service = HermesAdminService(db)
    projects, total = service.get_projects(status, limit, offset)
    return AdminProjectListOut(projects=projects, total=total)


@router.post("/projects", response_model=AdminProjectOut)
def create_project(
    payload: AdminProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Cria projeto administrativo."""
    service = HermesAdminService(db)
    return service.create_project(payload.model_dump(), user)


@router.patch("/projects/{project_id}", response_model=AdminProjectOut)
def update_project(
    project_id: int,
    payload: AdminProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Atualiza projeto administrativo."""
    service = HermesAdminService(db)
    project = service.update_project(project_id, payload.model_dump(exclude_unset=True), user)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Deleta projeto administrativo."""
    from app.models import AdminProject

    project = db.query(AdminProject).filter(AdminProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(project)
    db.commit()


@router.get("/routines", response_model=AdminRoutineListOut)
def get_routines(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista rotinas administrativas."""
    service = HermesAdminService(db)
    routines, total = service.get_routines(limit, offset)
    return AdminRoutineListOut(routines=routines, total=total)


@router.post("/routines", response_model=AdminRoutineOut)
def create_routine(
    payload: AdminRoutineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Cria rotina administrativa."""
    service = HermesAdminService(db)
    return service.create_routine(payload.model_dump(), user)


@router.patch("/routines/{routine_id}", response_model=AdminRoutineOut)
def update_routine(
    routine_id: int,
    payload: AdminRoutineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Atualiza rotina administrativa."""
    service = HermesAdminService(db)
    routine = service.update_routine(routine_id, payload.model_dump(exclude_unset=True), user)
    if not routine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
    return routine


@router.delete("/routines/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
    routine_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Deleta rotina administrativa."""
    from app.models import AdminRoutine

    routine = db.query(AdminRoutine).filter(AdminRoutine.id == routine_id).first()
    if not routine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Routine not found")
    db.delete(routine)
    db.commit()


@router.get("/memory", response_model=AdminMemoryListOut)
def get_memory(
    category: str | None = None,
    key: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista memória administrativa."""
    service = HermesAdminService(db)
    memories, total = service.get_memory(category, key, limit, offset)
    return AdminMemoryListOut(memories=memories, total=total)


@router.post("/memory", response_model=AdminMemoryOut)
def create_memory(
    payload: AdminMemoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Cria memória administrativa."""
    service = HermesAdminService(db)
    return service.create_memory(payload.model_dump(), user)


@router.patch("/memory/{memory_id}", response_model=AdminMemoryOut)
def update_memory(
    memory_id: int,
    payload: AdminMemoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Atualiza memória administrativa."""
    service = HermesAdminService(db)
    memory = service.update_memory(memory_id, payload.model_dump(exclude_unset=True), user)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.delete("/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Deleta memória administrativa."""
    from app.models import AdminMemory

    memory = db.query(AdminMemory).filter(AdminMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    db.delete(memory)
    db.commit()


@router.get("/logs", response_model=AdminActionLogListOut)
def get_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista logs de ações administrativas."""
    service = HermesAdminService(db)
    logs, total = service.get_logs(limit, offset)
    return AdminActionLogListOut(logs=logs, total=total)



@router.get("/skills", response_model=AdminSkillListOut)
def get_skills(
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Lista skills administrativas."""
    service = HermesAdminService(db)
    skills, total = service.get_skills(active_only, limit, offset)
    return AdminSkillListOut(skills=skills, total=total)


@router.post("/skills", response_model=AdminSkillOut)
def create_skill(
    payload: AdminSkillCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Cria skill administrativa."""
    service = HermesAdminService(db)
    return service.create_skill(payload.model_dump(), user)


@router.patch("/skills/{skill_id}", response_model=AdminSkillOut)
def update_skill(
    skill_id: int,
    payload: AdminSkillUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Atualiza skill administrativa."""
    service = HermesAdminService(db)
    skill = service.update_skill(skill_id, payload.model_dump(exclude_unset=True), user)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Deleta skill administrativa."""
    service = HermesAdminService(db)
    if not service.delete_skill(skill_id, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")


@router.post("/skills/{skill_id}/run", response_model=AdminSkillRunResponse)
async def run_skill(
    skill_id: int,
    payload: AdminSkillRunRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Executa uma skill administrativa."""
    from datetime import datetime, timezone
    service = HermesAdminService(db)
    result = await service.run_skill(skill_id, user, payload.parameters if payload else None)

    return AdminSkillRunResponse(
        skill_id=result["skill_id"],
        skill_name=result.get("skill_name", ""),
        status=result["status"],
        result=result.get("result"),
        error=result.get("error"),
        execution_time=result["execution_time"],
        executed_at=datetime.now(timezone.utc),
    )


@router.post("/skills/suggest")
async def suggest_skill(
    message: str,
    db: Session = Depends(get_db),
    user: User = Depends(_require_super_admin),
):
    """Sugere criação de skill a partir da conversa."""
    service = HermesAdminService(db)
    result = await service.suggest_skill_from_conversation(user, message)
    return result
