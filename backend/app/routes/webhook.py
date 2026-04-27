"""
Webhook do Telegram — multi-tenant.

Identificação do tenant em ordem de prioridade:
  1. /start tenant_X  → primeiro contato do cliente final, salva associação
  2. Chat já existente → usa o tenant que já estava associado
  3. Token do bot → tenant que tem aquele token (bot dedicado, premium)
  4. Fallback: tenant_id passado por query (compatibilidade legada)

Fluxo CRM (quando módulo CRM ativo no tenant):
  1. Busca lead pelo telefone → cria se não existir
  2. Vincula chat.lead_id ao lead
  3. Injeta contexto CRM no system prompt do Hermes
  4. Após reply, extrai e executa [[CRM:...]] do texto
  5. Envia reply limpo (sem comandos) ao cliente
"""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import Chat, Credit, Message, Tenant, UsageLog
from app.services.agent import build_context, maybe_create_task
from app.services.crm_agent import get_or_create_lead_from_chat, parse_and_execute_crm_commands
from app.services.deepseek import generate_reply
from app.services.telegram import send_telegram_message

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _extract_start_tenant(text: str) -> int | None:
    """Extrai tenant_id de '/start tenant_15' ou '/start 15'."""
    if not text:
        return None
    m = re.match(r"^/start\s+(?:tenant_)?(\d+)$", text.strip(), flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def _resolve_tenant_id(
    db: Session,
    *,
    chat_external_id: str,
    inbound_text: str,
    bot_token_received: str | None,
    fallback_query: int | None,
) -> int | None:
    # 1) /start tenant_X — primeiro contato
    start_tenant = _extract_start_tenant(inbound_text)
    if start_tenant:
        if db.query(Tenant).filter(Tenant.id == start_tenant, Tenant.active == True).first():
            return start_tenant

    # 2) Chat já existente neste channel
    existing = (
        db.query(Chat)
        .filter(Chat.channel == "telegram", Chat.chat_external_id == chat_external_id)
        .first()
    )
    if existing:
        return existing.tenant_id

    # 3) Bot dedicado: token bate com algum tenant
    if bot_token_received:
        t = db.query(Tenant).filter(Tenant.telegram_bot_token == bot_token_received).first()
        if t:
            return t.id

    # 4) Query param (compatibilidade)
    if fallback_query:
        if db.query(Tenant).filter(Tenant.id == fallback_query).first():
            return fallback_query

    return None


@router.post("/telegram")
async def telegram_webhook(
    payload: dict,
    tenant_id: int | None = Query(default=None),
    bot_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Recebe atualizações do Telegram.

    Aceita 3 formatos de URL (todos seguros):
      - /webhook/telegram                     (bot mestre, identifica via /start ou chat existente)
      - /webhook/telegram?tenant_id=X         (compatibilidade legada)
      - /webhook/telegram?bot_token=XXX       (bot dedicado por tenant)
    """
    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_external_id = str(message_data["chat"]["id"])
    contact_name = message_data.get("from", {}).get("first_name") or message_data["chat"].get("title")
    contact_phone = str(message_data.get("from", {}).get("id"))

    # 🛡️ PROTEÇÃO ANTI-PREJUÍZO: rejeita mensagem absurdamente longa
    settings_cfg = get_settings()
    if len(text) > settings_cfg.max_input_chars:
        await send_telegram_message(
            chat_external_id,
            f"⚠️ Sua mensagem é muito longa ({len(text)} caracteres). "
            f"Por favor, encurte para até {settings_cfg.max_input_chars} caracteres "
            f"e envie novamente. 🙏",
        )
        return {"status": "rejected", "reason": "input_too_long", "len": len(text)}

    resolved_tenant_id = _resolve_tenant_id(
        db,
        chat_external_id=chat_external_id,
        inbound_text=text,
        bot_token_received=bot_token,
        fallback_query=tenant_id,
    )
    if not resolved_tenant_id:
        settings = get_settings()
        if settings.hermes_master_bot_token:
            await send_telegram_message(
                chat_external_id,
                "👋 Olá! Para usar este atendimento, abra o link/QR Code que a empresa te enviou.",
            )
        return {"status": "no_tenant"}

    # Se foi /start tenant_X, normaliza pra mensagem inicial
    if _extract_start_tenant(text):
        inbound_text = "/start"
    else:
        inbound_text = text

    # ─── Chat: busca ou cria ──────────────────────────────────────────────────
    chat = (
        db.query(Chat)
        .filter(
            Chat.tenant_id == resolved_tenant_id,
            Chat.channel == "telegram",
            Chat.chat_external_id == chat_external_id,
        )
        .first()
    )
    if not chat:
        chat = Chat(
            tenant_id=resolved_tenant_id,
            channel="telegram",
            contact_name=contact_name,
            contact_phone=contact_phone,
            chat_external_id=chat_external_id,
            status="open",
        )
        db.add(chat)
        db.flush()

    inbound_message = Message(
        tenant_id=resolved_tenant_id,
        chat_id=chat.id,
        sender_type="user",
        content=inbound_text,
    )
    chat.contact_name = contact_name or chat.contact_name
    chat.contact_phone = contact_phone or chat.contact_phone
    chat.last_message = inbound_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(inbound_message)
    db.flush()

    # ─── CRM: busca/cria lead e vincula ao chat ───────────────────────────────
    lead = get_or_create_lead_from_chat(db, resolved_tenant_id, chat, inbound_text)

    # Tarefa automática (keywords como "ligar", "orçamento") — legado mantido
    maybe_create_task(db, resolved_tenant_id, inbound_text)

    # ─── Crédito: verifica antes de chamar a IA ───────────────────────────────
    credit = db.query(Credit).filter(Credit.tenant_id == resolved_tenant_id).first()
    if not credit:
        db.commit()
        return {"status": "no_credit_record"}
    if credit.remaining <= 0:
        db.commit()
        await send_telegram_message(
            chat.chat_external_id,
            "⚠️ Atendimento temporariamente indisponível. Tente novamente em breve.",
            tenant_id=resolved_tenant_id,
            db=db,
        )
        return {"status": "blocked", "reason": "no_credits"}
    if chat.ai_paused:
        db.commit()
        return {"status": "paused"}

    # ─── Hermes: gera resposta com contexto CRM ───────────────────────────────
    context = build_context(db, resolved_tenant_id, chat, lead=lead)
    reply_text, tokens_used = await generate_reply(context)

    # ─── CRM: executa comandos [[CRM:...]] e limpa o texto ───────────────────
    clean_reply = parse_and_execute_crm_commands(db, resolved_tenant_id, lead, reply_text)

    # ─── Salva resposta e debita crédito ─────────────────────────────────────
    outbound_message = Message(
        tenant_id=resolved_tenant_id,
        chat_id=chat.id,
        sender_type="assistant",
        content=clean_reply,
    )
    chat.last_message = clean_reply
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(outbound_message)
    db.flush()

    credit.used += 1
    credit.remaining -= 1
    db.add(UsageLog(
        tenant_id=resolved_tenant_id,
        message_id=outbound_message.id,
        tokens_used=tokens_used,
    ))
    db.commit()

    # Envia via bot dedicado do tenant (se tiver) ou bot mestre
    await send_telegram_message(
        chat.chat_external_id,
        clean_reply,
        tenant_id=resolved_tenant_id,
        db=db,
    )
    return {"status": "ok", "tenant_id": resolved_tenant_id, "crm_lead_id": lead.id if lead else None}
