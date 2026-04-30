"""
Rotas para Telegram Admin (Hermes Admin Master via Telegram).
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User
from app.services.hermes_admin import HermesAdminService
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/webhook", tags=["telegram-admin"])
logger = get_logger(__name__)


def _build_runtime_admin(user_name: str | None, *, role: str, email: str) -> User:
    return User(
        id=0,
        tenant_id=0,
        name=user_name or "Hermes Admin",
        email=email,
        role=role,
        is_super_admin=True,
        password="",
    )


def _matches_secret(received: str, primary: str, fallback: str | None = None) -> bool:
    candidates = [value for value in (primary, fallback) if value]
    return received in candidates


def _validate_optional_secret(received: str | None, primary: str, fallback: str | None = None) -> bool:
    if primary:
        return bool(received) and _matches_secret(received, primary, fallback)
    if received:
        return _matches_secret(received, fallback or "")
    return True


async def _handle_admin_webhook(
    payload: dict,
    *,
    expected_token: str,
    reply_token: str,
    role: str,
    email: str,
    db: Session,
) -> dict:
    if not expected_token:
        raise HTTPException(status_code=503, detail="Admin Telegram token not configured")

    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_id = str(message_data["chat"]["id"])
    user_name = message_data.get("from", {}).get("first_name") or message_data.get("chat", {}).get("title")

    service = HermesAdminService(db)
    admin_user = _build_runtime_admin(user_name, role=role, email=email)

    try:
        result = await service.chat(admin_user, text)
        reply_text = result.get("response", "Erro ao processar mensagem")
        await send_telegram_message(chat_id, reply_text, force_token=reply_token)
        return {"status": "ok", "response": reply_text}
    except (RuntimeError, ValueError) as exc:
        logger.warning("Telegram admin webhook failed for chat_id=%s role=%s: %s", chat_id, role, exc)
        error_msg = f"Erro ao processar mensagem: {str(exc)}"
        await send_telegram_message(chat_id, error_msg, force_token=reply_token)
        return {"status": "error", "error": error_msg}


@router.post("/telegram-admin")
async def telegram_admin_webhook(
    payload: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Webhook dedicado para o bot Telegram Admin.
    """
    settings = get_settings()
    if not _validate_optional_secret(
        x_telegram_bot_api_secret_token,
        settings.telegram_admin_webhook_secret,
        settings.telegram_admin_token,
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await _handle_admin_webhook(
        payload,
        expected_token=settings.telegram_admin_token,
        reply_token=settings.telegram_admin_token,
        role="super_admin",
        email="admin@hermes.com",
        db=db,
    )


@router.post("/telegram-master")
async def telegram_master_webhook(
    payload: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Webhook legado para o bot master já existente.
    """
    settings = get_settings()
    if not _validate_optional_secret(
        x_telegram_bot_api_secret_token,
        settings.hermes_master_webhook_secret,
        settings.hermes_master_bot_token,
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await _handle_admin_webhook(
        payload,
        expected_token=settings.hermes_master_bot_token,
        reply_token=settings.hermes_master_bot_token,
        role="master",
        email="master@hermes.com",
        db=db,
    )
