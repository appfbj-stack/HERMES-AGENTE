with open('backend/app/routes/admin_hermes.py', 'a', encoding='utf-8') as f:
    f.write('''


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
''')

print('Rotas de skills adicionadas ao admin_hermes.py!')
