from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Tenant, User, Credit
from ..schemas.auth import RegisterIn, LoginIn, TokenOut
from ..core.security import hash_password, verify_password, create_access_token
from ..config import settings


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _slugify(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")[:60] or "tenant"


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email já cadastrado")

    slug_base = _slugify(payload.tenant_name)
    slug = slug_base
    i = 1
    while db.query(Tenant).filter(Tenant.slug == slug).first():
        i += 1
        slug = f"{slug_base}-{i}"

    tenant = Tenant(name=payload.tenant_name, slug=slug, plan="free")
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role="owner",
    )
    db.add(user)
    db.add(Credit(tenant_id=tenant.id, balance=settings.initial_credits))
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenOut(
        access_token=token,
        user_id=user.id,
        tenant_id=tenant.id,
        name=user.name,
        email=user.email,
    )


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.email == payload.email, User.is_active == True)
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")

    token = create_access_token({"sub": str(user.id)})
    return TokenOut(
        access_token=token,
        user_id=user.id,
        tenant_id=user.tenant_id,
        name=user.name,
        email=user.email,
    )
