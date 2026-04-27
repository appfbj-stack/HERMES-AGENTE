from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import CrmActivityLog, Lead, User
from app.schemas import LeadCreate, LeadOut, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _log(db: Session, tenant_id: int, lead_id: int, action: str, detail: str, user_id: int) -> None:
    db.add(CrmActivityLog(tenant_id=tenant_id, lead_id=lead_id, user_id=user_id, action=action, detail=detail))


@router.get("", response_model=list[LeadOut])
def list_leads(
    status: str | None = Query(default=None, description="Filtrar por status"),
    origem: str | None = Query(default=None, description="Filtrar por origem"),
    responsavel_id: int | None = Query(default=None),
    search: str | None = Query(default=None, description="Busca por nome, telefone ou email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Lead).filter(Lead.tenant_id == current_user.tenant_id)
    if status:
        q = q.filter(Lead.status == status)
    if origem:
        q = q.filter(Lead.origem == origem)
    if responsavel_id:
        q = q.filter(Lead.responsavel_id == responsavel_id)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Lead.name.ilike(like) | Lead.phone.ilike(like) | Lead.email.ilike(like)
        )
    return q.order_by(Lead.created_at.desc()).all()


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Evita duplicata por telefone dentro do tenant
    if payload.phone:
        existing = db.query(Lead).filter(
            Lead.tenant_id == current_user.tenant_id,
            Lead.phone == payload.phone,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Lead com esse telefone já existe")

    lead = Lead(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(lead)
    db.flush()
    _log(db, current_user.tenant_id, lead.id, "lead_created", f"Lead criado: {lead.name}", current_user.id)
    db.commit()
    db.refresh(lead)
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    changes = []
    for k, v in payload.model_dump(exclude_unset=True).items():
        old = getattr(lead, k)
        if old != v:
            changes.append(f"{k}: {old} → {v}")
            setattr(lead, k, v)

    lead.updated_at = utcnow()
    if changes:
        _log(db, current_user.tenant_id, lead.id, "lead_updated", "; ".join(changes), current_user.id)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
