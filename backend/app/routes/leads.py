from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import Lead, User
from app.schemas import LeadCreate, LeadOut

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadOut])
def list_leads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Lead).filter(Lead.tenant_id == current_user.tenant_id).order_by(Lead.created_at.desc()).all()


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = Lead(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

