from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.deps import get_current_modules, get_current_tenant, get_current_user
from app.models import Credit, Tenant, TenantModule, User
from app.schemas import BootstrapRequest, LoginRequest, MeResponse, TenantModulesOut, TenantOut, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap", response_model=TokenResponse)
def bootstrap(payload: BootstrapRequest, db: Session = Depends(get_db)):
    existing = db.query(User).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bootstrap already completed")

    from app.core.config import get_settings

    settings = get_settings()
    if payload.token != settings.bootstrap_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")

    tenant = Tenant(name=payload.tenant_name, email=payload.tenant_email, plan=payload.plan, active=True)
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        name=payload.user_name,
        email=payload.user_email,
        password=get_password_hash(payload.password),
        role="admin",
        is_super_admin=True,  # primeiro user = dono do SaaS
    )
    db.add(user)
    db.add(Credit(tenant_id=tenant.id, total=payload.credits, used=0, remaining=payload.credits))
    db.add(TenantModule(tenant_id=tenant.id, crm=False))
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))


@router.get("/me", response_model=MeResponse)
def me(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    modules: TenantModule = Depends(get_current_modules),
):
    return MeResponse(
        user=UserOut.model_validate(current_user),
        tenant=TenantOut.model_validate(tenant),
        modules=TenantModulesOut(crm=modules.crm),
    )
