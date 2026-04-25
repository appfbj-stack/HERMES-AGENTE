from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Chat, Message, Credit, UsageLog, User
from ..schemas.chat import ChatOut, MessageOut, MessageIn, SendMessageOut
from ..core.deps import get_current_user
from ..services.deepseek import chat_completion


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Chat)
        .filter(Chat.tenant_id == user.tenant_id)
        .order_by(desc(Chat.last_message_at))
        .all()
    )


@router.post("", response_model=ChatOut)
def create_chat(
    contact_name: str = "Nova conversa",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = Chat(tenant_id=user.tenant_id, channel="web", contact_name=contact_name)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.tenant_id == user.tenant_id)
        .first()
    )
    if not chat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat não encontrado")
    return chat.messages


@router.post("/send", response_model=SendMessageOut)
async def send_message(
    payload: MessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    credit = db.query(Credit).filter(Credit.tenant_id == user.tenant_id).first()
    if not credit or credit.balance <= 0:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Créditos insuficientes")

    if payload.chat_id:
        chat = (
            db.query(Chat)
            .filter(Chat.id == payload.chat_id, Chat.tenant_id == user.tenant_id)
            .first()
        )
        if not chat:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat não encontrado")
    else:
        chat = Chat(tenant_id=user.tenant_id, channel="web", contact_name="Nova conversa")
        db.add(chat)
        db.flush()

    user_msg = Message(chat_id=chat.id, role="user", content=payload.content)
    db.add(user_msg)
    db.flush()

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

    assistant_msg = Message(
        chat_id=chat.id,
        role="assistant",
        content=result["content"],
        tokens_in=result["tokens_in"],
        tokens_out=result["tokens_out"],
    )
    db.add(assistant_msg)

    cost = max(1, (result["tokens_in"] + result["tokens_out"]) // 100)
    credit.balance = max(0, credit.balance - cost)
    from ..config import settings as _s
    db.add(
        UsageLog(
            tenant_id=user.tenant_id,
            chat_id=chat.id,
            provider=_s.llm_provider,
            model=result.get("model", _s.llm_model),
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost_credits=cost,
        )
    )
    chat.last_message_at = datetime.utcnow()

    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return SendMessageOut(
        chat_id=chat.id,
        user_message=user_msg,
        assistant_message=assistant_msg,
        credits_remaining=credit.balance,
    )
