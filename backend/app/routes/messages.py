from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.deps import get_current_credit, get_current_user
from app.models import Chat, CrmSetting, Message, TenantModule, UsageLog, User
from app.schemas import MessageOut, SendMessageRequest
from app.services.crm import ensure_crm_conversation, ensure_crm_defaults, ensure_crm_lead, sync_crm_message
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{chat_id}", response_model=list[MessageOut])
def list_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == current_user.tenant_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()


@router.post("/{chat_id}", response_model=MessageOut)
async def send_message(
    chat_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    credit=Depends(get_current_credit),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.tenant_id == current_user.tenant_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if credit.remaining <= 0:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="No credits remaining")

    message = Message(
        tenant_id=current_user.tenant_id,
        chat_id=chat.id,
        sender_type="human",
        content=payload.content,
    )
    chat.last_message = payload.content
    db.add(message)
    credit.used += 1
    credit.remaining -= 1
    db.flush()
    db.add(UsageLog(tenant_id=current_user.tenant_id, message_id=message.id, tokens_used=0))
    module = db.query(TenantModule).filter(TenantModule.tenant_id == current_user.tenant_id).first()
    if module and module.crm:
        ensure_crm_defaults(db, current_user.tenant_id)
        crm_settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == current_user.tenant_id).first()
        crm_lead = ensure_crm_lead(
            db,
            current_user.tenant_id,
            name=chat.contact_name or f"Contato {chat.chat_external_id}",
            phone=chat.contact_phone,
            origin=chat.channel,
        )
        crm_conversation = ensure_crm_conversation(db, current_user.tenant_id, chat, crm_lead)
        sync_crm_message(db, current_user.tenant_id, crm_conversation, message, chat.channel)
    db.commit()
    db.refresh(message)

    await send_telegram_message(chat.chat_external_id, payload.content)
    return message
