"""
Endpoints exclusivos do super admin (você, dono do SaaS).
Permite criar/listar/editar tenants (clientes).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.deps import get_current_user
from app.models import Credit, Tenant, TenantModule, User
from app.schemas import (
    CreditsAddRequest,
    TenantAdminOut,
    TenantCreateAdmin,
    TenantModuleUpdate,
    TenantUpdateAdmin,
)
from app.services.crm import ensure_crm_defaults
from app.services.modules import build_admin_modules_out, normalize_module_update

router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


@router.get("/master-bot")
def master_bot_info(_: User = Depends(lambda u=Depends(get_current_user): _check_super(u))):
    """Retorna o username do bot mestre pra gerar QR codes."""
    s = get_settings()
    return {
        "username": s.hermes_master_bot_username or None,
        "configured": bool(s.hermes_master_bot_token),
        "panel_url": s.public_panel_url,
    }


def _check_super(user: User) -> User:
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super admin only")
    return user


def _require_super_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    return user


def _to_admin_out(db: Session, tenant: Tenant) -> dict:
    credit = db.query(Credit).filter(Credit.tenant_id == tenant.id).first()
    mod = db.query(TenantModule).filter(TenantModule.tenant_id == tenant.id).first()
    payload = {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan": tenant.plan,
        "active": tenant.active,
        "niche": tenant.niche,
        "system_prompt": tenant.system_prompt,
        "telegram_bot_token": tenant.telegram_bot_token,
        "telegram_bot_username": tenant.telegram_bot_username,
        "created_at": tenant.created_at,
        "credits_total": credit.total if credit else 0,
        "credits_used": credit.used if credit else 0,
        "credits_remaining": credit.remaining if credit else 0,
    }
    payload.update(build_admin_modules_out(mod).model_dump())
    return payload


@router.get("/tenants", response_model=list[TenantAdminOut])
def list_tenants(
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    return [_to_admin_out(db, t) for t in tenants]


@router.post("/tenants", response_model=TenantAdminOut, status_code=201)
def create_tenant(
    payload: TenantCreateAdmin,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    if db.query(Tenant).filter(Tenant.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Tenant email já existe")
    if db.query(User).filter(User.email == payload.user_email).first():
        raise HTTPException(status_code=409, detail="User email já existe")
    if payload.telegram_bot_token and db.query(Tenant).filter(
        Tenant.telegram_bot_token == payload.telegram_bot_token
    ).first():
        raise HTTPException(status_code=409, detail="Bot token já cadastrado em outro tenant")

    tenant = Tenant(
        name=payload.name,
        email=payload.email,
        plan=payload.plan,
        niche=payload.niche,
        system_prompt=payload.system_prompt,
        telegram_bot_token=payload.telegram_bot_token,
        telegram_bot_username=payload.telegram_bot_username,
        active=True,
    )
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        name=payload.user_name,
        email=payload.user_email,
        password=get_password_hash(payload.user_password),
        role="admin",
    )
    db.add(user)

    credit = Credit(
        tenant_id=tenant.id,
        total=payload.credits,
        used=0,
        remaining=payload.credits,
    )
    db.add(credit)
    db.add(TenantModule(tenant_id=tenant.id))

    db.commit()
    db.refresh(tenant)
    return _to_admin_out(db, tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantAdminOut)
def update_tenant(
    tenant_id: int,
    payload: TenantUpdateAdmin,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(tenant, key, value)
    db.commit()
    db.refresh(tenant)
    return _to_admin_out(db, tenant)


@router.post("/tenants/{tenant_id}/credits", response_model=TenantAdminOut)
def add_credits(
    tenant_id: int,
    payload: CreditsAddRequest,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404)
    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        credit = Credit(tenant_id=tenant_id, total=0, used=0, remaining=0)
        db.add(credit)
        db.flush()
    credit.total += payload.amount
    credit.remaining += payload.amount
    db.commit()
    db.refresh(tenant)
    return _to_admin_out(db, tenant)


@router.patch("/tenants/{tenant_id}/modules", response_model=TenantAdminOut)
@router.put("/tenants/{tenant_id}/modules", response_model=TenantAdminOut)
def set_tenant_modules(
    tenant_id: int,
    payload: TenantModuleUpdate,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    """Ativa/desativa módulos (CRM, WhatsApp...) por tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404)

    mod = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    if not mod:
        mod = TenantModule(tenant_id=tenant_id)
        db.add(mod)

    module_data = normalize_module_update(payload)
    for k, v in module_data.items():
        setattr(mod, k, v)

    # Commit module changes first (separate from CRM init)
    db.commit()
    db.refresh(tenant)

    # Initialize CRM defaults in a separate transaction (non-critical)
    if module_data.get("crm"):
        try:
            ensure_crm_defaults(db, tenant_id)
            db.commit()
        except (SQLAlchemyError, ValueError):
            logger.exception("Erro ao inicializar CRM para tenant_id=%s", tenant_id)
            db.rollback()

    return _to_admin_out(db, tenant)


@router.delete("/tenants/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: int,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404)
    db.delete(tenant)
    db.commit()
    return None


@router.post("/tenants/{tenant_id}/reset-user-password")
def reset_user_password(
    tenant_id: int,
    payload: dict,
    _: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    """Redefine a senha do usuario admin de um tenant pelo super admin."""
    new_password = payload.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha minima de 6 caracteres")
    user = (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .order_by(User.id.asc())
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Nenhum usuario encontrado nesse tenant")
    user.password = get_password_hash(new_password)
    db.commit()
    return {"success": True, "user_id": user.id, "email": user.email}
