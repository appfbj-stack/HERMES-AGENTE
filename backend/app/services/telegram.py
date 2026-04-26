"""
Envia mensagens pelo Telegram.

Prioridade do token usado:
  1. Token dedicado do tenant (premium - tenant.telegram_bot_token)
  2. Token mestre (HERMES_MASTER_BOT_TOKEN)
  3. Token legado (TELEGRAM_BOT_TOKEN - compatibilidade)
"""
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Tenant


def _resolve_token(tenant_id: int | None, db: Session | None) -> str | None:
    settings = get_settings()
    if tenant_id and db:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant and tenant.telegram_bot_token:
            return tenant.telegram_bot_token
    return settings.hermes_master_bot_token or settings.telegram_bot_token or None


async def send_telegram_message(
    chat_external_id: str,
    text: str,
    *,
    tenant_id: int | None = None,
    db: Session | None = None,
) -> None:
    token = _resolve_token(tenant_id, db)
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_external_id, "text": text}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            await client.post(url, json=payload)
        except Exception as exc:  # noqa: BLE001
            print(f"[telegram] erro ao enviar: {exc}")


async def set_webhook(token: str, url: str) -> dict:
    """Configura webhook pra um bot específico."""
    api = f"https://api.telegram.org/bot{token}/setWebhook"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(api, json={"url": url})
        return r.json()


async def get_bot_info(token: str) -> dict:
    """Retorna info do bot (username, etc.)."""
    api = f"https://api.telegram.org/bot{token}/getMe"
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(api)
        return r.json()
