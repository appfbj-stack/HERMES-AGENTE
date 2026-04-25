from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Credit, Tenant, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = db.query(User).filter(User.id == int(payload["sub"]), User.tenant_id == int(payload["tenant_id"])).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id, Tenant.active.is_(True)).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
    return tenant


def get_current_credit(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)) -> Credit:
    credit = db.query(Credit).filter(Credit.tenant_id == tenant.id).first()
    if not credit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credits not configured")
    return credit


def get_webhook_tenant_id(x_tenant_id: str | None = Header(default=None), tenant_id: int | None = None) -> int:
    resolved = tenant_id or (int(x_tenant_id) if x_tenant_id else None)
    if not resolved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    return resolved

