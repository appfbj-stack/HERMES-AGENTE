"""
CRM Module — rotas integradas ao Hermes (sem duplicar auth/billing/planos).
Todas as rotas exigem:
  - login válido (get_current_user)
  - módulo CRM ativo no tenant (require_crm)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user, require_crm
from app.models import (
    Chat,
    Credit,
    CrmActivityLog,
    CrmFollowup,
    CrmKanbanColumn,
    CrmLeadTag,
    CrmSettings,
    CrmTag,
    Lead,
    Task,
    Tenant,
    TenantModule,
    UsageLog,
    User,
)
from app.schemas import (
    CrmActivityLogOut,
    CrmDashboardOut,
    CrmFollowupCreate,
    CrmFollowupOut,
    CrmFollowupUpdate,
    CrmKanbanColumnCreate,
    CrmKanbanColumnOut,
    CrmKanbanMoveRequest,
    CrmSettingsOut,
    CrmSettingsUpdate,
    CrmTagCreate,
    CrmTagOut,
    TenantModuleOut,
    TenantModuleUpdate,
)

router = APIRouter(prefix="/crm", tags=["crm"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _log_activity(
    db: Session,
    tenant_id: int,
    lead_id: int,
    action: str,
    detail: str | None = None,
    user_id: int | None = None,
) -> None:
    log = CrmActivityLog(
        tenant_id=tenant_id,
        lead_id=lead_id,
        user_id=user_id,
        action=action,
        detail=detail,
    )
    db.add(log)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=CrmDashboardOut)
def crm_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    tid = current_user.tenant_id
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)

    total_leads = db.query(func.count(Lead.id)).filter(Lead.tenant_id == tid).scalar() or 0
    leads_novos = (
        db.query(func.count(Lead.id))
        .filter(Lead.tenant_id == tid, Lead.status == "new")
        .scalar() or 0
    )
    atendimentos_abertos = (
        db.query(func.count(Chat.id))
        .filter(Chat.tenant_id == tid, Chat.status == "open")
        .scalar() or 0
    )
    followups_hoje = (
        db.query(func.count(CrmFollowup.id))
        .filter(
            CrmFollowup.tenant_id == tid,
            CrmFollowup.data_hora >= today_start,
            CrmFollowup.data_hora <= today_end,
            CrmFollowup.status == "pendente",
        )
        .scalar() or 0
    )
    conversas_ativas = (
        db.query(func.count(Chat.id))
        .filter(Chat.tenant_id == tid, Chat.status.in_(["open", "human"]))
        .scalar() or 0
    )
    fechamentos = (
        db.query(func.count(Lead.id))
        .filter(Lead.tenant_id == tid, Lead.status == "closed")
        .scalar() or 0
    )

    # Mensagens usadas no mês atual
    month_start = utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mensagens_mes = (
        db.query(func.sum(UsageLog.tokens_used))
        .filter(UsageLog.tenant_id == tid, UsageLog.created_at >= month_start)
        .scalar() or 0
    )

    credit = db.query(Credit).filter(Credit.tenant_id == tid).first()
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()

    return CrmDashboardOut(
        total_leads=total_leads,
        leads_novos=leads_novos,
        atendimentos_abertos=atendimentos_abertos,
        followups_hoje=followups_hoje,
        conversas_ativas=conversas_ativas,
        fechamentos=fechamentos,
        mensagens_usadas_mes=int(mensagens_mes),
        plano_atual=tenant.plan if tenant else "starter",
        creditos_restantes=credit.remaining if credit else 0,
    )


# ─── Kanban ───────────────────────────────────────────────────────────────────

@router.get("/kanban", response_model=list[CrmKanbanColumnOut])
def list_kanban_columns(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    return (
        db.query(CrmKanbanColumn)
        .filter(CrmKanbanColumn.tenant_id == current_user.tenant_id)
        .order_by(CrmKanbanColumn.position)
        .all()
    )


@router.post("/kanban", response_model=CrmKanbanColumnOut)
def create_kanban_column(
    payload: CrmKanbanColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    col = CrmKanbanColumn(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.patch("/kanban/{column_id}", response_model=CrmKanbanColumnOut)
def update_kanban_column(
    column_id: int,
    payload: CrmKanbanColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    col = (
        db.query(CrmKanbanColumn)
        .filter(CrmKanbanColumn.id == column_id, CrmKanbanColumn.tenant_id == current_user.tenant_id)
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(col, k, v)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/kanban/{column_id}", status_code=204)
def delete_kanban_column(
    column_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    col = (
        db.query(CrmKanbanColumn)
        .filter(CrmKanbanColumn.id == column_id, CrmKanbanColumn.tenant_id == current_user.tenant_id)
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    if col.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default columns")
    db.delete(col)
    db.commit()


@router.post("/kanban/move", status_code=200)
def move_lead_kanban(
    payload: CrmKanbanMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    col = (
        db.query(CrmKanbanColumn)
        .filter(CrmKanbanColumn.id == payload.column_id, CrmKanbanColumn.tenant_id == current_user.tenant_id)
        .first()
    )
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")

    old_col_id = lead.kanban_column_id
    lead.kanban_column_id = col.id
    lead.updated_at = utcnow()

    _log_activity(
        db,
        tenant_id=current_user.tenant_id,
        lead_id=lead.id,
        action="kanban_moved",
        detail=f"Movido para '{col.name}'",
        user_id=current_user.id,
    )
    db.commit()
    return {"ok": True, "lead_id": lead.id, "column_id": col.id}


# ─── Follow-ups ───────────────────────────────────────────────────────────────

@router.get("/followups", response_model=list[CrmFollowupOut])
def list_followups(
    lead_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    q = db.query(CrmFollowup).filter(CrmFollowup.tenant_id == current_user.tenant_id)
    if lead_id:
        q = q.filter(CrmFollowup.lead_id == lead_id)
    if status:
        q = q.filter(CrmFollowup.status == status)
    return q.order_by(CrmFollowup.data_hora.asc()).all()


@router.post("/followups", response_model=CrmFollowupOut)
def create_followup(
    payload: CrmFollowupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    # Verifica que o lead pertence ao tenant
    lead = db.query(Lead).filter(Lead.id == payload.lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    fu = CrmFollowup(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(fu)
    _log_activity(
        db,
        tenant_id=current_user.tenant_id,
        lead_id=payload.lead_id,
        action="followup_created",
        detail=f"Follow-up: {payload.titulo} em {payload.data_hora}",
        user_id=current_user.id,
    )
    db.commit()
    db.refresh(fu)
    return fu


@router.patch("/followups/{fu_id}", response_model=CrmFollowupOut)
def update_followup(
    fu_id: int,
    payload: CrmFollowupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    fu = db.query(CrmFollowup).filter(CrmFollowup.id == fu_id, CrmFollowup.tenant_id == current_user.tenant_id).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(fu, k, v)
    fu.updated_at = utcnow()
    db.commit()
    db.refresh(fu)
    return fu


@router.delete("/followups/{fu_id}", status_code=204)
def delete_followup(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    fu = db.query(CrmFollowup).filter(CrmFollowup.id == fu_id, CrmFollowup.tenant_id == current_user.tenant_id).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    db.delete(fu)
    db.commit()


# ─── Tags ─────────────────────────────────────────────────────────────────────

@router.get("/tags", response_model=list[CrmTagOut])
def list_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    return db.query(CrmTag).filter(CrmTag.tenant_id == current_user.tenant_id).order_by(CrmTag.name).all()


@router.post("/tags", response_model=CrmTagOut)
def create_tag(
    payload: CrmTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    tag = CrmTag(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    tag = db.query(CrmTag).filter(CrmTag.id == tag_id, CrmTag.tenant_id == current_user.tenant_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()


# Tags em leads (add/remove)

@router.post("/leads/{lead_id}/tags/{tag_id}", status_code=201)
def add_tag_to_lead(
    lead_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    tag = db.query(CrmTag).filter(CrmTag.id == tag_id, CrmTag.tenant_id == current_user.tenant_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    exists = db.query(CrmLeadTag).filter(CrmLeadTag.lead_id == lead_id, CrmLeadTag.tag_id == tag_id).first()
    if not exists:
        db.add(CrmLeadTag(tenant_id=current_user.tenant_id, lead_id=lead_id, tag_id=tag_id))
        db.commit()
    return {"ok": True}


@router.delete("/leads/{lead_id}/tags/{tag_id}", status_code=204)
def remove_tag_from_lead(
    lead_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    lt = db.query(CrmLeadTag).filter(CrmLeadTag.lead_id == lead_id, CrmLeadTag.tag_id == tag_id).first()
    if lt:
        db.delete(lt)
        db.commit()


# ─── Histórico de atividades de um lead ───────────────────────────────────────

@router.get("/leads/{lead_id}/activity", response_model=list[CrmActivityLogOut])
def get_lead_activity(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return (
        db.query(CrmActivityLog)
        .filter(CrmActivityLog.lead_id == lead_id, CrmActivityLog.tenant_id == current_user.tenant_id)
        .order_by(CrmActivityLog.created_at.desc())
        .all()
    )


# ─── Configurações do CRM ─────────────────────────────────────────────────────

@router.get("/settings", response_model=CrmSettingsOut)
def get_crm_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    settings = db.query(CrmSettings).filter(CrmSettings.tenant_id == current_user.tenant_id).first()
    if not settings:
        # Cria com defaults
        settings = CrmSettings(tenant_id=current_user.tenant_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.patch("/settings", response_model=CrmSettingsOut)
def update_crm_settings(
    payload: CrmSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_crm),
):
    settings = db.query(CrmSettings).filter(CrmSettings.tenant_id == current_user.tenant_id).first()
    if not settings:
        settings = CrmSettings(tenant_id=current_user.tenant_id)
        db.add(settings)

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(settings, k, v)
    settings.updated_at = utcnow()
    db.commit()
    db.refresh(settings)
    return settings


# ─── Módulos do tenant (admin) ────────────────────────────────────────────────

@router.get("/modules", response_model=TenantModuleOut)
def get_tenant_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna módulos ativos do tenant atual (sem exigir CRM ativo)."""
    mod = db.query(TenantModule).filter(TenantModule.tenant_id == current_user.tenant_id).first()
    if not mod:
        mod = TenantModule(tenant_id=current_user.tenant_id)
        db.add(mod)
        db.commit()
        db.refresh(mod)
    return mod
