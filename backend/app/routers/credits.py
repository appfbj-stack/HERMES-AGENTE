from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Credit, User, UsageLog
from ..schemas.common import CreditOut
from ..core.deps import get_current_user


router = APIRouter(prefix="/api/credits", tags=["credits"])


@router.get("", response_model=CreditOut)
def get_credits(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    credit = db.query(Credit).filter(Credit.tenant_id == user.tenant_id).first()
    if not credit:
        credit = Credit(tenant_id=user.tenant_id, balance=0)
        db.add(credit)
        db.commit()
        db.refresh(credit)
    return credit


@router.get("/usage")
def get_usage(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = (
        db.query(UsageLog)
        .filter(UsageLog.tenant_id == user.tenant_id)
        .order_by(UsageLog.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        "recent_logs": [
            {
                "id": l.id,
                "model": l.model,
                "tokens_in": l.tokens_in,
                "tokens_out": l.tokens_out,
                "cost_credits": l.cost_credits,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total_recent": sum(l.cost_credits for l in logs),
    }
