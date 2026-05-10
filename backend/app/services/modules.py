from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import TenantModule
from app.schemas import TenantAdminModulesOut, TenantModuleUpdate, TenantModulesOut

MODULE_KEY_ALIASES = {
    "crm": ("crm",),
    "whatsapp": ("whatsapp", "whatsapp_evolution"),
    "whatsapp_evolution": ("whatsapp_evolution", "whatsapp"),
    "kanban": ("kanban",),
    "agenda": ("agenda",),
    "followup": ("followup", "crm"),
    "instagram": ("instagram",),
    "youtube": ("youtube",),
    "content_publisher": ("content_publisher",),
    "agenda_pastoral": ("agenda_pastoral",),
}


def resolve_module_keys(module_key: str) -> tuple[str, ...]:
    return MODULE_KEY_ALIASES.get(module_key, (module_key,))


def module_enabled(modules: TenantModule, module_key: str) -> bool:
    return any(bool(getattr(modules, key, False)) for key in resolve_module_keys(module_key))


def has_module(db: Session, tenant_id: int, module_key: str) -> bool:
    modules = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    if not modules:
        return False
    return module_enabled(modules, module_key)


def build_modules_out(modules: TenantModule) -> TenantModulesOut:
    return TenantModulesOut(
        crm=bool(modules.crm),
        whatsapp=module_enabled(modules, "whatsapp"),
        whatsapp_evolution=module_enabled(modules, "whatsapp_evolution"),
        kanban=bool(modules.kanban),
        agenda=bool(modules.agenda),
        followup=module_enabled(modules, "followup"),
        instagram=bool(modules.instagram),
        youtube=bool(modules.youtube),
        content_publisher=bool(modules.content_publisher),
        agenda_pastoral=bool(modules.agenda_pastoral),
    )


def build_admin_modules_out(modules: TenantModule | None) -> TenantAdminModulesOut:
    return TenantAdminModulesOut(
        crm_enabled=bool(modules.crm) if modules else False,
        whatsapp_enabled=module_enabled(modules, "whatsapp") if modules else False,
        whatsapp_evolution_enabled=module_enabled(modules, "whatsapp_evolution") if modules else False,
        kanban_enabled=bool(modules.kanban) if modules else False,
        agenda_enabled=bool(modules.agenda) if modules else False,
        followup_enabled=module_enabled(modules, "followup") if modules else False,
        instagram_enabled=bool(modules.instagram) if modules else False,
        youtube_enabled=bool(modules.youtube) if modules else False,
        content_publisher_enabled=bool(modules.content_publisher) if modules else False,
        agenda_pastoral_enabled=bool(modules.agenda_pastoral) if modules else False,
    )


def normalize_module_update(payload: TenantModuleUpdate) -> dict[str, bool]:
    raw = payload.model_dump(exclude_unset=True)
    normalized: dict[str, bool] = {}
    for key, value in raw.items():
        if value is None:
            continue
        for resolved_key in resolve_module_keys(key):
            normalized[resolved_key] = value
    return normalized
