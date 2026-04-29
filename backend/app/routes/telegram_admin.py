"""
Rotas para Telegram Admin (Hermes Admin Master via Telegram)
"""
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import User
from app.services.hermes_admin import HermesAdminService
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/webhook", tags=["telegram-admin"])


def _identify_bot_from_token(x_telegram_bot_api_secret_token: str | None = Header(default=None)) -> str:
    """Identifica qual bot está sendo usado baseado no token do header"""
    settings = get_settings()
    
    if not x_telegram_bot_api_secret_token:
        raise HTTPException(status_code=400, detail="X-Telegram-Bot-Api-Secret-Token header required")
    
    token = x_telegram_bot_api_secret_token
    
    if token == settings.telegram_admin_token:
        return "admin"
    elif token == settings.hermes_master_bot_token:
        return "master"
    elif token == settings.telegram_bot_token:
        return "client"
    else:
        raise HTTPException(status_code=401, detail="Invalid bot token")


@router.post("/telegram-admin")
async def telegram_admin_webhook(
    payload: dict,
    x_telegram_bot_api_secret_token: str = Header(..., alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Webhook para Telegram Admin (Hermes Admin Master)
    
    Usa TELEGRAM_ADMIN_TOKEN para identificar o bot admin.
    O bot admin tem acesso global e usa GLM 4.7 (modelo mais forte).
    """
    settings = get_settings()
    
    # Validar token
    if x_telegram_bot_api_secret_token != settings.telegram_admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_id = str(message_data["chat"]["id"])
    user_name = message_data.get("from", {}).get("first_name") or message_data.get("chat").get("title")
    
    try:
        # Criar usuário admin temporário para o LLM Router
        admin_user = User(
            id=0,
            tenant_id=0,
            name=user_name or "Admin",
            email="admin@hermes.com",
            role="admin",
            is_super_admin=True,
            password=""
        )
        
        # Usar Hermes Admin Service
        service = HermesAdminService(db)
        result = await service.chat(admin_user, text)
        
        # Enviar resposta
        reply_text = result.get("response", "Erro ao processar mensagem")
        await send_telegram_message(chat_id, reply_text)
        
        return {"status": "ok", "response": reply_text}
        
    except Exception as exc:
        error_msg = f"Erro ao processar mensagem: {str(exc)}"
        await send_telegram_message(chat_id, error_msg)
        return {"status": "error", "error": error_msg}


@router.post("/telegram-master")
async def telegram_master_webhook(
    payload: dict,
    x_telegram_bot_api_secret_token: str = Header(..., alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    """
    Webhook para Telegram Master (Bot existente)
    
    Usa HERMES_MASTER_BOT_TOKEN para identificar o bot master.
    Comportamento mantido para compatibilidade.
    """
    settings = get_settings()
    
    # Validar token
    if x_telegram_bot_api_secret_token != settings.hermes_master_bot_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_id = str(message_data["chat"]["id"])
    user_name = message_data.get("from", {}).get("first_name") or message_data.get("chat").get("title")
    
    try:
        # Criar usuário admin temporário para o LLM Router
        admin_user = User(
            id=0,
            tenant_id=0,
            name=user_name or "Master",
            email="master@hermes.com",
            role="master",
            is_super_admin=True,
            password=""
        )
        
        # Usar Hermes Admin Service
        service = HermesAdminService(db)
        result = await service.chat(admin_user, text)
        
        # Enviar resposta
        reply_text = result.get("response", "Erro ao processar mensagem")
        await send_telegram_message(chat_id, reply_text)
        
        return {"status": "ok", "response": reply_text}
        
    except Exception as exc:
        error_msg = f"Erro ao processar mensagem: {str(exc)}"
        await send_telegram_message(chat_id, error_msg)
        return {"status": "error", "error": error_msg}