from __future__ import annotations

from app.models import TenantModule
from app.schemas import TenantAdminModulesOut, TenantModuleUpdate, TenantModulesOut

MODULE_KEY_ALIASES = {
    "crm": "crm",
    "whatsapp": "whatsapp",
    "whatsapp_evolution": "whatsapp",
    "kanban": "kanban",
    "agenda": "agenda",
    "followup": "crm",
    "instagram": "instagram",
    "youtube": "youtube",
    "content_publisher": "content_publisher",
}


def resolve_module_key(module_key: str) -> str:
    return MODULE_KEY_ALIASES.get(module_key, module_key)


def module_enabled(modules: TenantModule, module_key: str) -> bool:
    return bool(getattr(modules, resolve_module_key(module_key), False))


def build_modules_out(modules: TenantModule) -> TenantModulesOut:
    return TenantModulesOut(
        crm=bool(modules.crm),
        whatsapp=bool(modules.whatsapp),
        whatsapp_evolution=bool(modules.whatsapp),
        kanban=bool(modules.kanban),
        agenda=bool(modules.agenda),
        followup=bool(modules.crm),
        instagram=bool(modules.instagram),
        youtube=bool(modules.youtube),
        content_publisher=bool(modules.content_publisher),
    )


def build_admin_modules_out(modules: TenantModule | None) -> TenantAdminModulesOut:
    return TenantAdminModulesOut(
        crm_enabled=bool(modules.crm) if modules else False,
        whatsapp_enabled=bool(modules.whatsapp) if modules else False,
        whatsapp_evolution_enabled=bool(modules.whatsapp) if modules else False,
        kanban_enabled=bool(modules.kanban) if modules else False,
        agenda_enabled=bool(modules.agenda) if modules else False,
        followup_enabled=bool(modules.crm) if modules else False,
        instagram_enabled=bool(modules.instagram) if modules else False,
        youtube_enabled=bool(modules.youtube) if modules else False,
        content_publisher_enabled=bool(modules.content_publisher) if modules else False,
    )


def normalize_module_update(payload: TenantModuleUpdate) -> dict[str, bool]:
    raw = payload.model_dump(exclude_unset=True)
    normalized: dict[str, bool] = {}
    for key, value in raw.items():
        if value is None:
            continue
        normalized[resolve_module_key(key)] = value
    return normalized
