from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Chat, Message, Credit, UsageLog
from ..config import settings
from ..services.deepseek import chat_completion
from ..services.telegram import send_telegram_message
from ..services.whatsapp import send_whatsapp_message


router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _get_or_create_chat(
    db: Session, tenant_id: int, channel: str, external_id: str, name: str | None
) -> Chat:
    chat = (
        db.query(Chat)
        .filter(
            Chat.tenant_id == tenant_id,
            Chat.channel == channel,
            Chat.external_id == external_id,
        )
        .first()
    )
    if not chat:
        chat = Chat(
            tenant_id=tenant_id,
            channel=channel,
            external_id=external_id,
            contact_name=name,
        )
        db.add(chat)
        db.flush()
    return chat


async def _process_incoming(
    db: Session,
    tenant_id: int,
    channel: str,
    external_id: str,
    contact_name: str | None,
    text: str,
) -> str | None:
    chat = _get_or_create_chat(db, tenant_id, channel, external_id, contact_name)
    db.add(Message(chat_id=chat.id, role="user", content=text))
    db.flush()

    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit or credit.balance <= 0:
        chat.last_message_at = datetime.utcnow()
        db.commit()
        return None

    history = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    msgs = [
        {"role": "system", "content": "Você é um assistente útil em português brasileiro."}
    ] + [{"role": m.role, "content": m.content} for m in history]

    result = await chat_completion(msgs)
    db.add(
        Message(
            chat_id=chat.id,
            role="assistant",
            content=result["content"],
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
        )
    )
    cost = max(1, (result["tokens_in"] + result["tokens_out"]) // 100)
    credit.balance = max(0, credit.balance - cost)
    db.add(
        UsageLog(
            tenant_id=tenant_id,
            chat_id=chat.id,
            provider=settings.llm_provider,
            model=result.get("model", settings.llm_model),
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost_credits=cost,
        )
    )
    chat.last_message_at = datetime.utcnow()
    db.commit()
    return result["content"]


@router.post("/telegram/{tenant_id}")
async def telegram_webhook(
    tenant_id: int,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if (
        settings.telegram_webhook_secret
        and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")

    body = await request.json()
    msg = body.get("message") or body.get("edited_message")
    if not msg:
        return {"ok": True}

    text = msg.get("text", "")
    chat_id = str(msg["chat"]["id"])
    name = msg.get("from", {}).get("first_name", "Telegram")

    db = SessionLocal()
    try:
        reply = await _process_incoming(db, tenant_id, "telegram", chat_id, name, text)
        if reply:
            await send_telegram_message(chat_id, reply)
    finally:
        db.close()
    return {"ok": True}


@router.get("/whatsapp/{tenant_id}")
async def whatsapp_verify(tenant_id: int, request: Request):
    """Handshake de verificação Meta Cloud API."""
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.whatsapp_verify_token
    ):
        return int(params.get("hub.challenge", 0))
    raise HTTPException(status.HTTP_403_FORBIDDEN)


@router.post("/whatsapp/{tenant_id}")
async def whatsapp_webhook(tenant_id: int, request: Request):
    body = await request.json()
    db = SessionLocal()
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {}) or {}
                contacts = value.get("contacts") or [{}]
                for msg in value.get("messages", []) or []:
                    if msg.get("type") != "text":
                        continue
                    text = msg["text"]["body"]
                    from_ = msg["from"]
                    name = contacts[0].get("profile", {}).get("name")
                    reply = await _process_incoming(
                        db, tenant_id, "whatsapp", from_, name, text
                    )
                    if reply:
                        await send_whatsapp_message(from_, reply)
    finally:
        db.close()
    return {"ok": True}
