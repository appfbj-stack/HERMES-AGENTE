"""
Webhook do Telegram e WhatsApp (Evolution Go) com suporte multi-tenant.
"""
import re
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import Chat, Credit, CrmSetting, CrmWhatsAppConnection, Message, Tenant, TenantModule, UsageLog, User
from app.services.agent import (
    build_context,
    maybe_handle_task_query,
    maybe_handle_memory_query,
    merge_automation_confirmations,
    process_inbound_automation,
)
from app.services.billing_rules import can_use_ai, count_message
from app.services.crm import ensure_crm_conversation, ensure_crm_defaults, ensure_crm_lead, sync_crm_message
from app.services.crm_agent import get_or_create_lead_from_chat, parse_and_execute_crm_commands
from app.services.deepseek import generate_reply
from app.services.hermes_admin import HermesAdminService
from app.services.telegram import is_admin_token, send_telegram_message
from app.services.whatsapp_provider import WhatsAppProviderError, get_provider

router = APIRouter(prefix="/webhook", tags=["webhook"])

MAX_STORED_WEBHOOK_PAYLOAD_CHARS = 12000


def _extract_start_tenant(text: str) -> int | None:
    if not text:
        return None
    match = re.match(r"^/start\s+(?:tenant_)?(\d+)$", text.strip(), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _build_runtime_admin_user(name: str | None, *, role: str) -> User:
    return User(
        id=0,
        tenant_id=0,
        name=name or "Hermes Admin",
        email=f"{role}@hermes.local",
        role=role,
        is_super_admin=True,
        password="",
    )


async def _handle_admin_telegram_message(payload: dict, db: Session, token: str) -> dict:
    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_id = str(message_data["chat"]["id"])
    user_name = message_data.get("from", {}).get("first_name") or message_data.get("chat", {}).get("title")
    settings = get_settings()
    role = "master" if token == settings.hermes_master_bot_token else "super_admin"

    service = HermesAdminService(db)
    admin_user = _build_runtime_admin_user(user_name, role=role)
    result = await service.chat(admin_user, text)
    reply_text = result.get("response", "Erro ao processar mensagem")
    await send_telegram_message(chat_id, reply_text, force_token=token)
    return {"status": "ok", "scope": "admin", "response": reply_text}


def _resolve_tenant_id(
    db: Session,
    *,
    chat_external_id: str,
    inbound_text: str,
    bot_token_received: str | None,
    fallback_query: int | None,
) -> int | None:
    start_tenant = _extract_start_tenant(inbound_text)
    if start_tenant and db.query(Tenant).filter(Tenant.id == start_tenant, Tenant.active.is_(True)).first():
        return start_tenant

    existing = db.query(Chat).filter(Chat.channel == "telegram", Chat.chat_external_id == chat_external_id).first()
    if existing:
        return existing.tenant_id

    if bot_token_received:
        tenant = db.query(Tenant).filter(Tenant.telegram_bot_token == bot_token_received).first()
        if tenant:
            return tenant.id

    if fallback_query and db.query(Tenant).filter(Tenant.id == fallback_query).first():
        return fallback_query
    return None


def _extract_evolution_text(message_data: dict) -> str | None:
    if not isinstance(message_data, dict):
        return None
    if isinstance(message_data.get("conversation"), str):
        return message_data["conversation"].strip()
    extended = message_data.get("extendedTextMessage")
    if isinstance(extended, dict) and isinstance(extended.get("text"), str):
        return extended["text"].strip()
    for key in ("imageMessage", "videoMessage", "documentMessage"):
        item = message_data.get(key)
        if isinstance(item, dict) and isinstance(item.get("caption"), str):
            return item["caption"].strip()
    return None


def _extract_evolution_event(payload: dict) -> str | None:
    for key in ("event", "type", "webhookEvent"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return None


def _extract_evolution_key(payload: dict) -> dict:
    for root_key in ("key",):
        value = payload.get(root_key)
        if isinstance(value, dict):
            return value
    data = payload.get("data")
    if isinstance(data, dict):
        key = data.get("key")
        if isinstance(key, dict):
            return key
    message = payload.get("message")
    if isinstance(message, dict):
        key = message.get("key")
        if isinstance(key, dict):
            return key
    return {}


def _extract_evolution_message(payload: dict) -> dict:
    direct = payload.get("message")
    if isinstance(direct, dict):
        nested = direct.get("message")
        if isinstance(nested, dict):
            return nested
        return direct
    data = payload.get("data")
    if isinstance(data, dict):
        direct = data.get("message")
        if isinstance(direct, dict):
            nested = direct.get("message")
            if isinstance(nested, dict):
                return nested
            return direct
    return {}


def _extract_push_name(payload: dict) -> str | None:
    for key in ("pushName", "push_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("pushName", "push_name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _serialize_webhook_payload(payload: dict) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=True)
    except (TypeError, ValueError):
        text = str(payload)
    if len(text) <= MAX_STORED_WEBHOOK_PAYLOAD_CHARS:
        return text
    return text[: MAX_STORED_WEBHOOK_PAYLOAD_CHARS - 3] + "..."


def _track_whatsapp_webhook(
    connection: CrmWhatsAppConnection,
    payload: dict,
    *,
    event: str | None,
) -> None:
    connection.last_webhook_event = event or "unknown"
    connection.last_webhook_payload = _serialize_webhook_payload(payload)
    connection.last_webhook_at = datetime.now(timezone.utc)


def _normalize_whatsapp_number(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = str(raw).split("@")[0].strip()
    return cleaned or None


def _extract_evolution_instance_name(payload: dict) -> str | None:
    for key in ("instanceName", "instance", "instance_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    instance_data = payload.get("instance")
    if isinstance(instance_data, dict):
        for key in ("instanceName", "name", "instance"):
            value = instance_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


@router.post("/telegram")
async def telegram_webhook(
    payload: dict,
    tenant_id: int | None = Query(default=None),
    bot_token: str | None = Query(default=None),
    x_telegram_bot_api_secret_token: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: Session = Depends(get_db),
):
    message_data = payload.get("message") or payload.get("edited_message")
    if not message_data:
        return {"status": "ignored", "reason": "no_message"}

    text = (message_data.get("text") or "").strip()
    if not text:
        return {"status": "ignored", "reason": "no_text"}

    chat_external_id = str(message_data["chat"]["id"])
    contact_name = message_data.get("from", {}).get("first_name") or message_data["chat"].get("title")
    contact_phone = str(message_data.get("from", {}).get("id"))

    settings_cfg = get_settings()
    if len(text) > settings_cfg.max_input_chars:
        await send_telegram_message(
            chat_external_id,
            f"⚠️ Sua mensagem é muito longa ({len(text)} caracteres). Por favor, encurte para até {settings_cfg.max_input_chars} caracteres.",
        )
        return {"status": "rejected", "reason": "input_too_long", "len": len(text)}

    token_hint = x_telegram_bot_api_secret_token or bot_token
    if is_admin_token(token_hint):
        return await _handle_admin_telegram_message(payload, db, token_hint)

    resolved_tenant_id = _resolve_tenant_id(
        db,
        chat_external_id=chat_external_id,
        inbound_text=text,
        bot_token_received=token_hint,
        fallback_query=tenant_id,
    )
    if not resolved_tenant_id:
        if settings_cfg.hermes_master_bot_token:
            await send_telegram_message(chat_external_id, "👋 Olá! Para usar este atendimento, abra o link/QR Code que a empresa te enviou.")
        return {"status": "no_tenant"}

    inbound_text = "/start" if _extract_start_tenant(text) else text

    chat = db.query(Chat).filter(Chat.tenant_id == resolved_tenant_id, Chat.channel == "telegram", Chat.chat_external_id == chat_external_id).first()
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

    inbound_message = Message(tenant_id=resolved_tenant_id, chat_id=chat.id, sender_type="user", content=inbound_text)
    chat.contact_name = contact_name or chat.contact_name
    chat.contact_phone = contact_phone or chat.contact_phone
    chat.last_message = inbound_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(inbound_message)
    db.flush()

    lead = get_or_create_lead_from_chat(db, resolved_tenant_id, chat, inbound_text)
    automation_confirmations = process_inbound_automation(db, resolved_tenant_id, chat, inbound_text)

    module = db.query(TenantModule).filter(TenantModule.tenant_id == resolved_tenant_id).first()
    crm_conversation = None
    crm_lead = None
    if module and module.crm:
        ensure_crm_defaults(db, resolved_tenant_id)
        crm_lead = ensure_crm_lead(
            db,
            resolved_tenant_id,
            name=chat.contact_name or f"Contato {chat.chat_external_id}",
            phone=chat.contact_phone,
            origin=chat.channel,
            notes=inbound_text[:500],
        )
        crm_conversation = ensure_crm_conversation(db, resolved_tenant_id, chat, crm_lead)
        sync_crm_message(db, resolved_tenant_id, crm_conversation, inbound_message, chat.channel)

    credit = db.query(Credit).filter(Credit.tenant_id == resolved_tenant_id).first()
    if not credit:
        db.commit()
        return {"status": "no_credit_record"}
    if credit.remaining <= 0:
        db.commit()
        await send_telegram_message(chat.chat_external_id, "⚠️ Atendimento temporariamente indisponível. Tente novamente em breve.", tenant_id=resolved_tenant_id, db=db)
        return {"status": "blocked", "reason": "no_credits"}
    if chat.ai_paused:
        db.commit()
        return {"status": "paused"}
    if module and module.crm:
        crm_settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == resolved_tenant_id).first()
        if crm_settings and not crm_settings.hermes_enabled:
            db.commit()
            return {"status": "crm_hermes_disabled"}
        
        # Verificar regras de negócio para IA
        can_use, reason = can_use_ai(db, resolved_tenant_id)
        if not can_use:
            db.commit()
            await send_telegram_message(
                chat.chat_external_id,
                f"⚠️ {reason if reason else 'IA temporariamente indisponível'}.",
                tenant_id=resolved_tenant_id,
                db=db
            )
            return {"status": "ai_blocked", "reason": reason}

    direct_task_reply = maybe_handle_task_query(db, resolved_tenant_id, chat, inbound_text)
    direct_memory_reply = maybe_handle_memory_query(db, resolved_tenant_id, chat, inbound_text) if direct_task_reply is None else None
    tokens_used = 0
    if direct_task_reply is not None:
        clean_reply = merge_automation_confirmations(direct_task_reply, automation_confirmations)
    elif direct_memory_reply is not None:
        clean_reply = merge_automation_confirmations(direct_memory_reply, automation_confirmations)
    else:
        context = build_context(db, resolved_tenant_id, chat, lead=lead)
        reply_text, tokens_used = await generate_reply(context, tenant_id=resolved_tenant_id)
        clean_reply = parse_and_execute_crm_commands(db, resolved_tenant_id, lead, reply_text)
        clean_reply = merge_automation_confirmations(clean_reply, automation_confirmations)

    outbound_message = Message(tenant_id=resolved_tenant_id, chat_id=chat.id, sender_type="assistant", content=clean_reply)
    chat.last_message = clean_reply
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(outbound_message)
    db.flush()

    if crm_conversation:
        sync_crm_message(db, resolved_tenant_id, crm_conversation, outbound_message, chat.channel)

    # Contabilizar mensagem usando serviço de regras de negócio
    count_message(db, resolved_tenant_id)
    db.add(UsageLog(tenant_id=resolved_tenant_id, message_id=outbound_message.id, tokens_used=tokens_used))
    db.commit()

    await send_telegram_message(chat.chat_external_id, clean_reply, tenant_id=resolved_tenant_id, db=db)
    return {"status": "ok", "tenant_id": resolved_tenant_id, "crm_lead_id": lead.id if lead else None}


@router.post("/evolution-go")
async def evolution_go_webhook(
    payload: dict,
    tenant_id: int | None = Query(default=None),
    instance_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    event = _extract_evolution_event(payload)
    if event and event not in {"messages.upsert", "messages_upsert", "message.upsert", "message_received"}:
        return {"status": "ignored", "reason": f"unsupported_event:{event}"}

    resolved_instance_name = instance_name or _extract_evolution_instance_name(payload)
    connection_query = db.query(CrmWhatsAppConnection)
    if tenant_id is not None:
        connection_query = connection_query.filter(CrmWhatsAppConnection.tenant_id == tenant_id)
    if resolved_instance_name:
        connection_query = connection_query.filter(CrmWhatsAppConnection.instance_name == resolved_instance_name)
    connection = connection_query.first()
    if not connection:
        return {"status": "ignored", "reason": "connection_not_found"}
    _track_whatsapp_webhook(connection, payload, event=event)

    key_data = _extract_evolution_key(payload)
    if key_data.get("fromMe") is True:
        db.commit()
        return {"status": "ignored", "reason": "from_me"}

    message_root = _extract_evolution_message(payload)
    inbound_text = _extract_evolution_text(message_root)
    if not inbound_text:
        db.commit()
        return {"status": "ignored", "reason": "unsupported_message"}

    tenant_id = connection.tenant_id
    remote_jid = _normalize_whatsapp_number(
        key_data.get("remoteJid")
        or payload.get("remoteJid")
        or (payload.get("data") or {}).get("remoteJid")
    )
    if not remote_jid:
        db.commit()
        return {"status": "ignored", "reason": "missing_remote_jid"}

    contact_name = _extract_push_name(payload)
    chat = db.query(Chat).filter(Chat.tenant_id == tenant_id, Chat.channel == "whatsapp", Chat.chat_external_id == remote_jid).first()
    if not chat:
        chat = Chat(
            tenant_id=tenant_id,
            channel="whatsapp",
            contact_name=contact_name,
            contact_phone=remote_jid,
            chat_external_id=remote_jid,
            status="open",
        )
        db.add(chat)
        db.flush()

    inbound_message = Message(tenant_id=tenant_id, chat_id=chat.id, sender_type="user", content=inbound_text)
    chat.contact_name = contact_name or chat.contact_name
    chat.contact_phone = remote_jid or chat.contact_phone
    chat.last_message = inbound_text
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(inbound_message)
    db.flush()

    lead = get_or_create_lead_from_chat(db, tenant_id, chat, inbound_text)
    automation_confirmations = process_inbound_automation(db, tenant_id, chat, inbound_text)

    module = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    crm_conversation = None
    if module and module.crm:
        ensure_crm_defaults(db, tenant_id)
        crm_lead = ensure_crm_lead(
            db,
            tenant_id,
            name=chat.contact_name or f"Contato {remote_jid}",
            phone=chat.contact_phone,
            origin="whatsapp",
            notes=inbound_text[:500],
        )
        crm_conversation = ensure_crm_conversation(db, tenant_id, chat, crm_lead)
        sync_crm_message(db, tenant_id, crm_conversation, inbound_message, chat.channel)

    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credits not configured for tenant")
    if credit.remaining <= 0:
        db.commit()
        return {"status": "blocked", "reason": "no_credits"}
    if chat.ai_paused:
        db.commit()
        return {"status": "paused"}
    if module and module.crm:
        crm_settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == tenant_id).first()
        if crm_settings and not crm_settings.hermes_enabled:
            db.commit()
            return {"status": "crm_hermes_disabled"}
        
        # Verificar regras de negócio para IA
        can_use, reason = can_use_ai(db, tenant_id)
        if not can_use:
            db.commit()
            return {"status": "ai_blocked", "reason": reason}

    direct_task_reply = maybe_handle_task_query(db, tenant_id, chat, inbound_text)
    direct_memory_reply = maybe_handle_memory_query(db, tenant_id, chat, inbound_text) if direct_task_reply is None else None
    tokens_used = 0
    if direct_task_reply is not None:
        clean_reply = merge_automation_confirmations(direct_task_reply, automation_confirmations)
    elif direct_memory_reply is not None:
        clean_reply = merge_automation_confirmations(direct_memory_reply, automation_confirmations)
    else:
        context = build_context(db, tenant_id, chat, lead=lead)
        reply_text, tokens_used = await generate_reply(context, tenant_id=tenant_id)
        clean_reply = parse_and_execute_crm_commands(db, tenant_id, lead, reply_text)
        clean_reply = merge_automation_confirmations(clean_reply, automation_confirmations)

    outbound_message = Message(tenant_id=tenant_id, chat_id=chat.id, sender_type="assistant", content=clean_reply)
    chat.last_message = clean_reply
    chat.last_message_at = datetime.now(timezone.utc)
    db.add(outbound_message)
    db.flush()

    if crm_conversation:
        sync_crm_message(db, tenant_id, crm_conversation, outbound_message, chat.channel)

    # Contabilizar mensagem usando serviço de regras de negócio
    count_message(db, tenant_id)
    db.add(UsageLog(tenant_id=tenant_id, message_id=outbound_message.id, tokens_used=tokens_used))
    db.commit()

    try:
        await get_provider(connection).send_text(connection, remote_jid, clean_reply)
    except (WhatsAppProviderError, Exception):
        connection.last_error = "Webhook processed but outbound WhatsApp reply failed"
        db.commit()
        return {"status": "partial", "reason": "reply_not_sent"}

    return {"status": "ok"}
