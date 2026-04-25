from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Chat, Credit, Message, UsageLog
from app.services.agent import build_context, maybe_create_lead, maybe_create_task
from app.services.deepseek import generate_reply
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/telegram")
async def telegram_webhook(
    payload: dict,
    tenant_id: int = Query(...),
    db: Session = Depends(get_db),
):
    message_data = payload.get("message")
    if not message_data or "text" not in message_data:
        return {"status": "ignored"}

    chat_external_id = str(message_data["chat"]["id"])
    inbound_text = message_data["text"].strip()
    contact_name = message_data.get("from", {}).get("first_name") or message_data["chat"].get("title")
    contact_phone = str(message_data.get("from", {}).get("id"))

    chat = (
        db.query(Chat)
        .filter(Chat.tenant_id == tenant_id, Chat.channel == "telegram", Chat.chat_external_id == chat_external_id)
        .first()
    )
    if not chat:
        chat = Chat(
            tenant_id=tenant_id,
            channel="telegram",
            contact_name=contact_name,
            contact_phone=contact_phone,
            chat_external_id=chat_external_id,
            status="open",
        )
        db.add(chat)
        db.flush()

    inbound_message = Message(tenant_id=tenant_id, chat_id=chat.id, sender_type="user", content=inbound_text)
    chat.contact_name = contact_name or chat.contact_name
    chat.contact_phone = contact_phone or chat.contact_phone
    chat.last_message = inbound_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(inbound_message)
    db.flush()

    maybe_create_lead(db, tenant_id, chat, inbound_text)
    maybe_create_task(db, tenant_id, inbound_text)

    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credits not configured for tenant")
    if credit.remaining <= 0:
        db.commit()
        return {"status": "blocked", "reason": "no_credits"}
    if chat.ai_paused:
        db.commit()
        return {"status": "paused"}

    context = build_context(db, tenant_id, chat)
    reply_text, tokens_used = await generate_reply(context)

    outbound_message = Message(tenant_id=tenant_id, chat_id=chat.id, sender_type="assistant", content=reply_text)
    chat.last_message = reply_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(outbound_message)
    db.flush()

    credit.used += 1
    credit.remaining -= 1
    db.add(UsageLog(tenant_id=tenant_id, message_id=outbound_message.id, tokens_used=tokens_used))
    db.commit()

    await send_telegram_message(chat.chat_external_id, reply_text)
    return {"status": "ok"}

