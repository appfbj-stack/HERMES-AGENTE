"""
Envia mensagens pelo Telegram.

Prioridade padrão do token usado:
  1. Token forçado explicitamente
  2. Token dedicado do tenant (tenant.telegram_bot_token)
  3. Token mestre (HERMES_MASTER_BOT_TOKEN)
  4. Token cliente global (TELEGRAM_CLIENT_TOKEN / TELEGRAM_BOT_TOKEN)
"""
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import Tenant

logger = get_logger(__name__)


def get_client_token() -> str | None:
    settings = get_settings()
    return settings.telegram_client_token or settings.telegram_bot_token or None


def get_admin_token() -> str | None:
    settings = get_settings()
    return settings.telegram_admin_token or settings.hermes_master_bot_token or None


def is_admin_token(token: str | None) -> bool:
    if not token:
        return False
    settings = get_settings()
    return token in {settings.telegram_admin_token, settings.hermes_master_bot_token}


def _resolve_token(tenant_id: int | None, db: Session | None, force_token: str | None = None) -> str | None:
    if force_token:
        return force_token

    settings = get_settings()
    if tenant_id and db:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant and tenant.telegram_bot_token:
            return tenant.telegram_bot_token
    return settings.hermes_master_bot_token or get_client_token() or None


async def send_telegram_message(
    chat_external_id: str,
    text: str,
    *,
    tenant_id: int | None = None,
    db: Session | None = None,
    force_token: str | None = None,
) -> None:
    token = _resolve_token(tenant_id, db, force_token=force_token)
    if not token:
        logger.warning("Telegram token ausente para envio chat_external_id=%s tenant_id=%s", chat_external_id, tenant_id)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_external_id, "text": text}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok", False):
                logger.warning(
                    "Telegram API retornou erro lógico chat_external_id=%s tenant_id=%s response=%s",
                    chat_external_id,
                    tenant_id,
                    data,
                )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro ao enviar mensagem Telegram chat_external_id=%s tenant_id=%s", chat_external_id, tenant_id)


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
