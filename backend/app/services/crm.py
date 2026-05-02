import json
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Chat,
    CrmActivityLog,
    CrmConversation,
    CrmKanbanColumn,
    CrmLead,
    CrmLeadTag,
    CrmMessage,
    CrmSetting,
    CrmTag,
    Message,
    Tenant,
    TenantModule,
    UsageLog,
    User,
)

DEFAULT_KANBAN_COLUMNS = [
    ("Novo lead", "#DCEBFF"),
    ("Em atendimento", "#DDF7E5"),
    ("Aguardando resposta", "#FFF1C2"),
    ("Orçamento enviado", "#FFE1CC"),
    ("Fechado", "#D7F7E8"),
    ("Perdido", "#F8D7DA"),
]

DEFAULT_TAGS = ["quente", "frio", "orçamento", "cliente antigo", "urgente", "retorno"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def dumps_json(value) -> str:
    return json.dumps(value, ensure_ascii=True)


def loads_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def get_or_create_tenant_module(db: Session, tenant_id: int) -> TenantModule:
    module = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    if module:
        return module

    module = TenantModule(tenant_id=tenant_id, crm=False)
    db.add(module)
    db.flush()
    return module


def ensure_crm_defaults(db: Session, tenant_id: int) -> None:
    """Garante que o tenant tenha configurações, colunas e tags padrão do CRM.

    Cada bloco é protegido individualmente com flush + except para evitar que
    erros de constraint (race condition) ou schema desatualizado bloqueiem os
    outros blocos e os routes CRM como um todo.
    """
    # --- CrmSetting ---
    try:
        settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == tenant_id).first()
        if not settings:
            db.add(
                CrmSetting(
                    tenant_id=tenant_id,
                    status_options_json=dumps_json([item[0] for item in DEFAULT_KANBAN_COLUMNS]),
                    tags_json=dumps_json(DEFAULT_TAGS),
                    business_hours_json=dumps_json(
                        {
                            "timezone": "America/Sao_Paulo",
                            "weekdays": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                            "start": "08:00",
                            "end": "18:00",
                        }
                    ),
                    hermes_enabled=True,
                )
            )
            db.flush()
    except SQLAlchemyError:
        db.rollback()

    # --- CrmKanbanColumn ---
    try:
        existing_columns = (
            db.query(CrmKanbanColumn)
            .filter(CrmKanbanColumn.tenant_id == tenant_id)
            .order_by(CrmKanbanColumn.position.asc())
            .all()
        )
        if not existing_columns:
            for index, (name, color) in enumerate(DEFAULT_KANBAN_COLUMNS):
                db.add(
                    CrmKanbanColumn(
                        tenant_id=tenant_id,
                        name=name,
                        position=index,
                        color=color,
                        is_default=True,
                    )
                )
            db.flush()
    except SQLAlchemyError:
        db.rollback()

    # --- CrmTag ---
    try:
        existing_tags = db.query(CrmTag).filter(CrmTag.tenant_id == tenant_id).count()
        if existing_tags == 0:
            for name in DEFAULT_TAGS:
                db.add(CrmTag(tenant_id=tenant_id, name=name))
            db.flush()
    except SQLAlchemyError:
        db.rollback()


def serialize_settings(settings: CrmSetting) -> dict:
    return {
        "id": settings.id,
        "tenant_id": settings.tenant_id,
        "status_options": loads_json(settings.status_options_json, [item[0] for item in DEFAULT_KANBAN_COLUMNS]),
        "tags": loads_json(settings.tags_json, DEFAULT_TAGS),
        "initial_auto_message": settings.initial_auto_message,
        "business_hours": loads_json(settings.business_hours_json, {}),
        "hermes_enabled": settings.hermes_enabled,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }


def log_crm_activity(
    db: Session,
    tenant_id: int,
    action: str,
    description: str | None = None,
    *,
    lead_id: int | None = None,
    conversation_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        CrmActivityLog(
            tenant_id=tenant_id,
            lead_id=lead_id,
            conversation_id=conversation_id,
            action=action,
            description=description,
            metadata_json=dumps_json(metadata) if metadata else None,
        )
    )


def replace_lead_tags(db: Session, tenant_id: int, lead_id: int, tag_ids: list[int]) -> None:
    db.query(CrmLeadTag).filter(CrmLeadTag.tenant_id == tenant_id, CrmLeadTag.lead_id == lead_id).delete()
    valid_tags = (
        db.query(CrmTag)
        .filter(CrmTag.tenant_id == tenant_id, CrmTag.id.in_(tag_ids))
        .all()
        if tag_ids
        else []
    )
    for tag in valid_tags:
        db.add(CrmLeadTag(tenant_id=tenant_id, lead_id=lead_id, tag_id=tag.id))


def get_lead_tags(db: Session, tenant_id: int, lead_ids: list[int]) -> dict[int, list[CrmTag]]:
    if not lead_ids:
        return {}
    links = db.query(CrmLeadTag).filter(CrmLeadTag.tenant_id == tenant_id, CrmLeadTag.lead_id.in_(lead_ids)).all()
    if not links:
        return {}
    tags = db.query(CrmTag).filter(CrmTag.tenant_id == tenant_id).all()
    tag_map = {tag.id: tag for tag in tags}
    result: dict[int, list[CrmTag]] = {lead_id: [] for lead_id in lead_ids}
    for link in links:
        tag = tag_map.get(link.tag_id)
        if tag:
            result.setdefault(link.lead_id, []).append(tag)
    return result


def serialize_lead(lead: CrmLead, tags: list[CrmTag]) -> dict:
    return {
        "id": lead.id,
        "tenant_id": lead.tenant_id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "origin": lead.origin,
        "status": lead.status,
        "responsible_user_id": lead.responsible_user_id,
        "notes": lead.notes,
        "last_contact_at": lead.last_contact_at,
        "kanban_column_id": lead.kanban_column_id,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
        "tags": tags,
    }


def ensure_crm_lead(
    db: Session,
    tenant_id: int,
    *,
    name: str,
    phone: str | None,
    email: str | None = None,
    origin: str = "manual",
    notes: str | None = None,
) -> CrmLead:
    lead = None
    if phone:
        lead = db.query(CrmLead).filter(CrmLead.tenant_id == tenant_id, CrmLead.phone == phone).first()
    if lead:
        lead.name = name or lead.name
        lead.email = email or lead.email
        lead.origin = origin or lead.origin
        lead.notes = notes or lead.notes
        lead.last_contact_at = now_utc()
        return lead

    lead = CrmLead(
        tenant_id=tenant_id,
        name=name,
        phone=phone,
        email=email,
        origin=origin,
        notes=notes,
        last_contact_at=now_utc(),
    )
    db.add(lead)
    db.flush()
    log_crm_activity(db, tenant_id, "lead.created", "Lead criado automaticamente", lead_id=lead.id)
    return lead


def ensure_crm_conversation(db: Session, tenant_id: int, chat: Chat, lead: CrmLead | None) -> CrmConversation:
    conversation = (
        db.query(CrmConversation)
        .filter(
            CrmConversation.tenant_id == tenant_id,
            CrmConversation.channel == chat.channel,
            CrmConversation.external_id == chat.chat_external_id,
        )
        .first()
    )
    if conversation:
        conversation.lead_id = lead.id if lead else conversation.lead_id
        conversation.chat_id = chat.id
        conversation.contact_name = chat.contact_name
        conversation.contact_phone = chat.contact_phone
        conversation.status = chat.status
        conversation.ai_enabled = not chat.ai_paused
        conversation.assigned_user_id = chat.assigned_user_id
        conversation.last_message = chat.last_message
        conversation.last_message_at = chat.last_message_at
        return conversation

    conversation = CrmConversation(
        tenant_id=tenant_id,
        lead_id=lead.id if lead else None,
        chat_id=chat.id,
        channel=chat.channel,
        external_id=chat.chat_external_id,
        contact_name=chat.contact_name,
        contact_phone=chat.contact_phone,
        status=chat.status,
        ai_enabled=not chat.ai_paused,
        assigned_user_id=chat.assigned_user_id,
        last_message=chat.last_message,
        last_message_at=chat.last_message_at,
    )
    db.add(conversation)
    db.flush()
    log_crm_activity(
        db,
        tenant_id,
        "conversation.created",
        "Conversa sincronizada no CRM",
        lead_id=conversation.lead_id,
        conversation_id=conversation.id,
    )
    return conversation


def sync_crm_message(
    db: Session,
    tenant_id: int,
    conversation: CrmConversation,
    message: Message,
    channel: str,
) -> CrmMessage:
    existing = (
        db.query(CrmMessage)
        .filter(CrmMessage.tenant_id == tenant_id, CrmMessage.legacy_message_id == message.id)
        .first()
    )
    if existing:
        return existing

    crm_message = CrmMessage(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        legacy_message_id=message.id,
        sender_type=message.sender_type,
        channel=channel,
        content=message.content,
        created_at=message.created_at,
        updated_at=message.created_at,
    )
    db.add(crm_message)
    return crm_message


def sync_existing_chat_to_crm(db: Session, tenant_id: int, chat: Chat) -> CrmConversation:
    lead = ensure_crm_lead(
        db,
        tenant_id,
        name=chat.contact_name or f"Contato {chat.chat_external_id}",
        phone=chat.contact_phone,
        origin=chat.channel,
    )
    conversation = ensure_crm_conversation(db, tenant_id, chat, lead)
    messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()
    for message in messages:
        sync_crm_message(db, tenant_id, conversation, message, chat.channel)
    return conversation


def get_messages_used_month(db: Session, tenant_id: int) -> int:
    month_start = now_utc().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        return (
            db.query(UsageLog)
            .filter(UsageLog.tenant_id == tenant_id, UsageLog.created_at >= month_start)
            .count()
        )
    except SQLAlchemyError:
        # Legacy databases may still be missing usage_logs.created_at during rollout.
        return 0


def get_user_name_map(db: Session, tenant_id: int) -> dict[int, str]:
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    return {user.id: user.name for user in users}


def get_tenant_plan(db: Session, tenant_id: int) -> str:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant.plan if tenant else "-"
