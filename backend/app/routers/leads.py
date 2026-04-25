from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lead, User
from ..schemas.common import LeadIn, LeadOut
from ..core.deps import get_current_user


router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
def list_leads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Lead)
        .filter(Lead.tenant_id == user.tenant_id)
        .order_by(Lead.created_at.desc())
        .all()
    )


@router.post("", response_model=LeadOut)
def create_lead(
    payload: LeadIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = Lead(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == user.tenant_id)
        .first()
    )
    if not lead:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(lead, k, v)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.tenant_id == user.tenant_id)
        .first()
    )
    if not lead:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    db.delete(lead)
    db.commit()
    return {"ok": True}
