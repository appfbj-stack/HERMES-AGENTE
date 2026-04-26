"""
Endpoints públicos pra chat web (sem autenticação).

URL pública pro cliente final:
  https://meuchat.fbautomacao.space/c/{tenant_id}

A página chama os endpoints aqui pra:
  - Identificar a empresa atendida (GET /public/tenant/{id})
  - Buscar histórico de mensagens da sessão (GET /public/chat/{tenant_id}/messages?session_id=xxx)
  - Enviar mensagem e receber resposta da IA (POST /public/chat/{tenant_id}/send)

A "sessão" é um UUID gerado no navegador e guardado no localStorage do cliente final.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import Chat, Credit, Message, Tenant, UsageLog
from app.services.agent import build_context, maybe_create_lead, maybe_create_task
from app.services.deepseek import generate_reply

router = APIRouter(prefix="/public", tags=["public"])


# ============================================================
# Schemas
# ============================================================
class PublicTenantInfo(BaseModel):
    id: int
    name: str
    niche: str | None
    welcome: str = "Olá! Como posso te ajudar hoje?"
    bot_display_name: str = "Assistente Pessoal"
    active: bool


class PublicMessage(BaseModel):
    id: int
    sender_type: str
    content: str
    created_at: datetime


class PublicSendRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    visitor_name: str | None = None
    content: str = Field(min_length=1)


class PublicSendResponse(BaseModel):
    user_message: PublicMessage
    assistant_message: PublicMessage | None = None
    blocked: bool = False
    blocked_reason: str | None = None


# ============================================================
# Endpoints
# ============================================================
@router.get("/tenant/{tenant_id}", response_model=PublicTenantInfo)
def public_tenant_info(tenant_id: int, db: Session = Depends(get_db)):
    """Retorna info pública pra mostrar no header do chat."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return PublicTenantInfo(
        id=tenant.id,
        name=tenant.name,
        niche=tenant.niche,
        active=tenant.active,
    )


@router.get("/chat/{tenant_id}/messages", response_model=list[PublicMessage])
def list_session_messages(
    tenant_id: int,
    session_id: str = Query(..., min_length=8, max_length=128),
    db: Session = Depends(get_db),
):
    """Histórico do chat da sessão atual (pra continuar conversa após reload)."""
    chat = (
        db.query(Chat)
        .filter(
            Chat.tenant_id == tenant_id,
            Chat.channel == "web",
            Chat.chat_external_id == session_id,
        )
        .first()
    )
    if not chat:
        return []
    msgs = (
        db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()
    )
    return [
        PublicMessage(
            id=m.id, sender_type=m.sender_type, content=m.content, created_at=m.created_at
        )
        for m in msgs
    ]


@router.post("/chat/{tenant_id}/send", response_model=PublicSendResponse)
async def public_chat_send(
    tenant_id: int,
    payload: PublicSendRequest,
    db: Session = Depends(get_db),
):
    """Cliente final envia mensagem. IA responde se houver crédito e tenant ativo."""
    settings = get_settings()
    text = payload.content.strip()

    # 🛡️ Limite de input
    if len(text) > settings.max_input_chars:
        raise HTTPException(
            status_code=413,
            detail=f"Mensagem muito longa. Máximo {settings.max_input_chars} caracteres.",
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    if not tenant.active:
        raise HTTPException(status_code=403, detail="Atendimento temporariamente indisponível")

    # Cria/recupera o chat por session_id
    chat = (
        db.query(Chat)
        .filter(
            Chat.tenant_id == tenant_id,
            Chat.channel == "web",
            Chat.chat_external_id == payload.session_id,
        )
        .first()
    )
    if not chat:
        chat = Chat(
            tenant_id=tenant_id,
            channel="web",
            chat_external_id=payload.session_id,
            contact_name=payload.visitor_name or "Visitante",
            status="open",
        )
        db.add(chat)
        db.flush()
    elif payload.visitor_name and not chat.contact_name:
        chat.contact_name = payload.visitor_name

    # Salva mensagem do cliente final
    user_msg = Message(
        tenant_id=tenant_id,
        chat_id=chat.id,
        sender_type="user",
        content=text,
    )
    chat.last_message = text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(user_msg)
    db.flush()

    maybe_create_lead(db, tenant_id, chat, text)
    maybe_create_task(db, tenant_id, text)

    # Verifica créditos
    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit or credit.remaining <= 0:
        db.commit()
        return PublicSendResponse(
            user_message=PublicMessage(
                id=user_msg.id,
                sender_type=user_msg.sender_type,
                content=user_msg.content,
                created_at=user_msg.created_at,
            ),
            blocked=True,
            blocked_reason="Atendimento temporariamente indisponível. Tente novamente em breve.",
        )

    if chat.ai_paused:
        db.commit()
        return PublicSendResponse(
            user_message=PublicMessage(
                id=user_msg.id,
                sender_type=user_msg.sender_type,
                content=user_msg.content,
                created_at=user_msg.created_at,
            ),
            blocked=True,
            blocked_reason="Sua mensagem foi recebida. Em breve um atendente humano responderá.",
        )

    # Chama IA
    context = build_context(db, tenant_id, chat)
    reply_text, tokens_used = await generate_reply(context)

    bot_msg = Message(
        tenant_id=tenant_id,
        chat_id=chat.id,
        sender_type="assistant",
        content=reply_text,
    )
    chat.last_message = reply_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(bot_msg)
    db.flush()

    credit.used += 1
    credit.remaining -= 1
    db.add(UsageLog(tenant_id=tenant_id, message_id=bot_msg.id, tokens_used=tokens_used))
    db.commit()

    return PublicSendResponse(
        user_message=PublicMessage(
            id=user_msg.id,
            sender_type=user_msg.sender_type,
            content=user_msg.content,
            created_at=user_msg.created_at,
        ),
        assistant_message=PublicMessage(
            id=bot_msg.id,
            sender_type=bot_msg.sender_type,
            content=bot_msg.content,
            created_at=bot_msg.created_at,
        ),
    )
