from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import ClientMemory, ClientProfile, ClientSkill, User
from app.schemas import ClientProfileOut, ClientProfileUpdate, ClientSkillActivationRequest, ClientSkillCreate, ClientSkillOut, ClientSkillToggleRequest, ClientSuggestionOut
from app.services.agent import activate_client_skill

router = APIRouter(prefix="/client", tags=["client"])


@router.get("/profile", response_model=ClientProfileOut)
def get_client_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(ClientProfile).filter(ClientProfile.tenant_id == current_user.tenant_id).first()
    if not profile:
        profile = ClientProfile(tenant_id=current_user.tenant_id, nivel_automacao="medio")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=ClientProfileOut)
def update_client_profile(
    payload: ClientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(ClientProfile).filter(ClientProfile.tenant_id == current_user.tenant_id).first()
    if not profile:
        profile = ClientProfile(tenant_id=current_user.tenant_id, nivel_automacao="medio")
        db.add(profile)
        db.flush()

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/skills", response_model=list[ClientSkillOut])
def list_client_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == current_user.tenant_id)
        .order_by(ClientSkill.created_at.desc())
        .all()
    )


@router.get("/suggestions", response_model=list[ClientSuggestionOut])
def list_client_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    insight_rows = (
        db.query(ClientMemory)
        .filter(
            ClientMemory.tenant_id == current_user.tenant_id,
            ClientMemory.tipo == "insight",
            ClientMemory.chave.like("suggestion:%"),
        )
        .order_by(ClientMemory.updated_at.desc())
        .all()
    )
    active_skill_names = {
        item.nome_skill
        for item in db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == current_user.tenant_id, ClientSkill.ativa.is_(True))
        .all()
    }

    suggestions: list[ClientSuggestionOut] = []
    for row in insight_rows:
        try:
            import json

            parsed = json.loads(row.valor)
        except Exception:
            parsed = {"message": row.valor}
        skill_key = row.chave.replace("suggestion:", "", 1)
        suggestions.append(
            ClientSuggestionOut(
                skill_key=skill_key,
                message=str(parsed.get("message", row.valor)),
                suggested_at=parsed.get("suggested_at"),
                active=skill_key in active_skill_names,
            )
        )
    return suggestions


@router.post("/skills", response_model=ClientSkillOut, status_code=status.HTTP_201_CREATED)
def create_client_skill(
    payload: ClientSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = ClientSkill(
        tenant_id=current_user.tenant_id,
        nome_skill=payload.nome_skill,
        descricao=payload.descricao,
        ativa=payload.ativa,
        configuracao=payload.configuracao,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.post("/skills/activate", response_model=ClientSkillOut)
def activate_client_skill_route(
    payload: ClientSkillActivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = activate_client_skill(db, current_user.tenant_id, payload.skill_key)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill sugerida não encontrada")
    db.commit()
    skill = (
        db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == current_user.tenant_id, ClientSkill.nome_skill == payload.skill_key)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao ativar skill")
    return skill


@router.post("/skills/{skill_id}/toggle", response_model=ClientSkillOut)
def toggle_client_skill(
    skill_id: int,
    payload: ClientSkillToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = (
        db.query(ClientSkill)
        .filter(ClientSkill.id == skill_id, ClientSkill.tenant_id == current_user.tenant_id)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill não encontrada")

    skill.ativa = payload.ativa
    db.commit()
    db.refresh(skill)
    return skill
