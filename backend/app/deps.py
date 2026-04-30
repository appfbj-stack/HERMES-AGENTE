from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Credit, Tenant, TenantModule, User
from app.services.crm import ensure_crm_defaults, get_or_create_tenant_module

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


def get_current_modules(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)) -> TenantModule:
    module = get_or_create_tenant_module(db, tenant.id)
    db.flush()
    return module


def has_module(modules: TenantModule, module_key: str) -> bool:
    return bool(getattr(modules, module_key, False))


def tenant_has_module(db: Session, tenant_id: int, module_key: str) -> bool:
    modules = get_or_create_tenant_module(db, tenant_id)
    db.flush()
    return has_module(modules, module_key)


def require_module_enabled(module_key: str, label: str):
    def dependency(modules: TenantModule = Depends(get_current_modules)) -> TenantModule:
        if not has_module(modules, module_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Módulo {label} não está ativo neste plano. Fale com o suporte.",
            )
        return modules

    return dependency


def require_crm_module(modules: TenantModule = Depends(require_module_enabled("crm", "CRM"))) -> TenantModule:
    return modules


def require_whatsapp_module(
    modules: TenantModule = Depends(require_module_enabled("whatsapp", "WhatsApp"))
) -> TenantModule:
    return modules


def require_kanban_module(
    modules: TenantModule = Depends(require_module_enabled("kanban", "Kanban"))
) -> TenantModule:
    return modules


def require_instagram_module(
    modules: TenantModule = Depends(require_module_enabled("instagram", "Instagram"))
) -> TenantModule:
    return modules


def require_youtube_module(
    modules: TenantModule = Depends(require_module_enabled("youtube", "YouTube"))
) -> TenantModule:
    return modules


def require_content_publisher_module(
    modules: TenantModule = Depends(require_module_enabled("content_publisher", "Content Publisher"))
) -> TenantModule:
    return modules


def require_crm_or_whatsapp_module(modules: TenantModule = Depends(get_current_modules)) -> TenantModule:
    if not (modules.crm or modules.whatsapp):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Módulo CRM ou WhatsApp não está ativo neste plano. Fale com o suporte.",
        )
    return modules


def ensure_crm_ready(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    modules: TenantModule = Depends(require_crm_module),
) -> TenantModule:
    ensure_crm_defaults(db, tenant.id)
    db.flush()
    return modules


def require_crm(
    _: TenantModule = Depends(ensure_crm_ready),
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_master_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_super_admin and current_user.role != "master":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master access required")
    return current_user


def get_webhook_tenant_id(x_tenant_id: str | None = Header(default=None), tenant_id: int | None = None) -> int:
    resolved = tenant_id or (int(x_tenant_id) if x_tenant_id else None)
    if not resolved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
    return resolved
