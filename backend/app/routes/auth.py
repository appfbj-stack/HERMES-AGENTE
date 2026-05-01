from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.deps import get_current_modules, get_current_tenant, get_current_user
from app.models import Credit, Tenant, TenantModule, User
from app.schemas import AdminSeedSyncRequest, BootstrapRequest, LoginRequest, MeResponse, TenantModulesOut, TenantOut, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def _normalize_secret(value: str | None) -> str:
    normalized = (value or "").strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"'}:
        normalized = normalized[1:-1].strip()
    return normalized


def _get_normalized_env_admin() -> tuple[str, str]:
    settings = get_settings()
    return _normalize_email(_normalize_secret(settings.admin_email)), _normalize_secret(settings.admin_password)


def _sync_env_admin_if_needed(db: Session, email: str) -> None:
    admin_email, _ = _get_normalized_env_admin()
    if not admin_email or _normalize_email(email) != admin_email:
        return

    from app.main import ensure_env_super_admin

    ensure_env_super_admin()
    db.expire_all()


def _get_active_user_by_email(db: Session, email: str) -> User | None:
    users = (
        db.query(User)
        .join(Tenant, Tenant.id == User.tenant_id)
        .filter(func.lower(User.email) == email, Tenant.active.is_(True))
        .order_by(User.is_super_admin.desc(), User.id.asc())
        .all()
    )
    if len(users) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esse email existe em mais de uma empresa. Informe também o email da empresa.",
        )
    return users[0] if users else None


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
    settings = get_settings()
    email = _normalize_email(payload.email)
    tenant_email = _normalize_email(payload.tenant_email)
    env_admin_email, env_admin_password = _get_normalized_env_admin()

    if email == env_admin_email and payload.password == env_admin_password:
        _sync_env_admin_if_needed(db, email)
        admin_user = _get_active_user_by_email(db, email)
        if admin_user:
            return TokenResponse(access_token=create_access_token(str(admin_user.id), admin_user.tenant_id))

    user = None
    if tenant_email:
        tenant = db.query(Tenant).filter(func.lower(Tenant.email) == tenant_email).first()
        if tenant and not tenant.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
        if not tenant:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email da empresa não encontrado")
        user = db.query(User).filter(User.tenant_id == tenant.id, func.lower(User.email) == email).first()
    else:
        user = _get_active_user_by_email(db, email)
        if not user:
            inactive_user = (
                db.query(User)
                .join(Tenant, Tenant.id == User.tenant_id)
                .filter(func.lower(User.email) == email, Tenant.active.is_(False))
                .first()
            )
            if inactive_user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")

    if not user:
        _sync_env_admin_if_needed(db, email)
        if tenant_email:
            tenant = db.query(Tenant).filter(func.lower(Tenant.email) == tenant_email).first()
            if tenant and tenant.active:
                user = db.query(User).filter(User.tenant_id == tenant.id, func.lower(User.email) == email).first()
        else:
            user = _get_active_user_by_email(db, email)

    password_valid = bool(user) and verify_password(payload.password, user.password)

    # Recovery path for the env-seeded super admin if the stored hash drifted.
    if (
        user
        and not password_valid
        and env_admin_email
        and env_admin_password
        and _normalize_email(user.email) == env_admin_email
        and payload.password == env_admin_password
    ):
        _sync_env_admin_if_needed(db, email)
        db.refresh(user)
        user.password = get_password_hash(env_admin_password)
        user.role = "admin"
        user.is_super_admin = True
        db.add(user)
        db.commit()
        db.refresh(user)
        password_valid = True

    if not user or not password_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos")

    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))


@router.post("/sync-admin-env")
def sync_admin_env(payload: AdminSeedSyncRequest):
    from app.main import sync_env_super_admin

    settings = get_settings()
    if payload.token != settings.bootstrap_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")
    return sync_env_super_admin()


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout stateless para o frontend encerrar a sessão local."""
    return {"success": True, "message": "Logout realizado com sucesso"}


@router.get("/me", response_model=MeResponse)
def me(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
    modules: TenantModule = Depends(get_current_modules),
):
    return MeResponse(
        user=UserOut.model_validate(current_user),
        tenant=TenantOut.model_validate(tenant),
        modules=TenantModulesOut(
            crm=modules.crm,
            whatsapp=modules.whatsapp,
            kanban=modules.kanban,
            agenda=modules.agenda,
            instagram=modules.instagram,
            youtube=modules.youtube,
            content_publisher=modules.content_publisher,
        ),
    )


@router.get("/modules", response_model=TenantModulesOut)
def get_modules(
    current_user: User = Depends(get_current_user),
    modules: TenantModule = Depends(get_current_modules),
):
    """Retorna apenas os módulos ativos do tenant atual."""
    return TenantModulesOut(
        crm=modules.crm,
        whatsapp=modules.whatsapp,
        kanban=modules.kanban,
        agenda=modules.agenda,
        instagram=modules.instagram,
        youtube=modules.youtube,
        content_publisher=modules.content_publisher,
    )
