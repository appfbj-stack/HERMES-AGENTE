from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import (
    ensure_crm_ready,
    get_current_modules,
    get_current_tenant,
    get_current_user,
    require_kanban_module,
    require_whatsapp_module,
)
from app.models import (
    Chat,
    Credit,
    CrmActivityLog,
    CrmConversation,
    CrmFollowUp,
    CrmKanbanColumn,
    CrmLead,
    CrmMessage,
    CrmSetting,
    CrmTag,
    CrmTask,
    CrmWhatsAppConnection,
    Message,
    Tenant,
    UsageLog,
    User,
)
from app.schemas import (
    CrmActivityLogOut,
    CrmConversationMessageCreate,
    CrmConversationOut,
    CrmConversationStateUpdate,
    CrmDashboardOut,
    CrmFollowUpCreate,
    CrmFollowUpOut,
    CrmFollowUpUpdate,
    CrmKanbanBoardOut,
    CrmKanbanCardOut,
    CrmKanbanColumnCreate,
    CrmKanbanColumnOut,
    CrmKanbanMoveRequest,
    CrmLeadCreate,
    CrmLeadOut,
    CrmLeadUpdate,
    CrmMessageOut,
    CrmModuleUpdate,
    CrmSettingsOut,
    CrmSettingsUpdate,
    CrmTagCreate,
    CrmTagOut,
    CrmTaskCreate,
    CrmTaskOut,
    CrmTaskUpdate,
    CrmWhatsAppConnectionOut,
    CrmWhatsAppConnectionUpsert,
    CrmWhatsAppStatusOut,
    TenantModulesOut,
)
from app.services.crm import (
    ensure_crm_defaults,
    ensure_crm_lead,
    get_lead_tags,
    get_messages_used_month,
    get_or_create_tenant_module,
    log_crm_activity,
    replace_lead_tags,
    serialize_lead,
    serialize_settings,
    sync_crm_message,
)
from app.services.modules import build_modules_out
from app.services.telegram import send_telegram_message
from app.services.whatsapp_provider import WhatsAppProviderError, get_provider

router = APIRouter(prefix="/crm", tags=["crm"])
protected = APIRouter(dependencies=[Depends(ensure_crm_ready)])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_count(query) -> int:
    try:
        return query.count()
    except SQLAlchemyError:
        return 0


def _serialize_whatsapp_connection(connection: CrmWhatsAppConnection) -> CrmWhatsAppConnectionOut:
    return CrmWhatsAppConnectionOut(
        id=connection.id,
        tenant_id=connection.tenant_id,
        provider=connection.provider,
        instance_name=connection.instance_name,
        api_base_url=connection.api_base_url,
        webhook_url=connection.webhook_url,
        status=connection.status,
        connected_phone=connection.connected_phone,
        qr_code_base64=connection.qr_code_base64,
        last_error=connection.last_error,
        last_webhook_event=connection.last_webhook_event,
        last_webhook_payload=connection.last_webhook_payload,
        last_webhook_at=connection.last_webhook_at,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.get("/modules", response_model=TenantModulesOut)
@router.get("/module", response_model=TenantModulesOut)
def get_crm_modules(modules=Depends(get_current_modules)):
    return build_modules_out(modules)


@router.put("/module", response_model=TenantModulesOut)
def update_crm_module(
    payload: CrmModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    module = get_or_create_tenant_module(db, current_user.tenant_id)
    module.crm = payload.crm
    if payload.crm:
        ensure_crm_defaults(db, current_user.tenant_id)
    db.commit()
    db.refresh(module)
    return build_modules_out(module)


@router.get("/whatsapp", response_model=CrmWhatsAppConnectionOut | None, dependencies=[Depends(require_whatsapp_module)])
def get_crm_whatsapp_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    return _serialize_whatsapp_connection(connection) if connection else None


@router.put("/whatsapp", response_model=CrmWhatsAppConnectionOut, dependencies=[Depends(require_whatsapp_module)])
def upsert_crm_whatsapp_connection(
    payload: CrmWhatsAppConnectionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    if not connection:
        connection = CrmWhatsAppConnection(tenant_id=current_user.tenant_id, provider=payload.provider, instance_name=payload.instance_name)
        db.add(connection)

    connection.provider = payload.provider
    connection.instance_name = payload.instance_name
    connection.api_base_url = payload.api_base_url
    connection.api_key = payload.api_key
    connection.webhook_url = payload.webhook_url
    db.commit()
    db.refresh(connection)
    return _serialize_whatsapp_connection(connection)


@router.post("/whatsapp/connect", response_model=CrmWhatsAppStatusOut, dependencies=[Depends(require_whatsapp_module)])
async def connect_crm_whatsapp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="WhatsApp connection is not configured")
    try:
        result = await get_provider(connection).connect(connection)
        connection.status = result.status
        connection.connected_phone = result.connected_phone
        connection.qr_code_base64 = result.qr_code_base64
        connection.last_error = None
        db.commit()
        return CrmWhatsAppStatusOut(
            status=result.status,
            connected_phone=result.connected_phone,
            qr_code_base64=result.qr_code_base64,
            raw=result.raw,
        )
    except (WhatsAppProviderError, httpx.HTTPError) as exc:
        connection.status = "error"
        connection.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/whatsapp/status", response_model=CrmWhatsAppStatusOut, dependencies=[Depends(require_whatsapp_module)])
async def get_crm_whatsapp_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="WhatsApp connection is not configured")
    try:
        result = await get_provider(connection).get_status(connection)
        connection.status = result.status
        connection.connected_phone = result.connected_phone
        if result.qr_code_base64:
            connection.qr_code_base64 = result.qr_code_base64
        connection.last_error = None
        db.commit()
        return CrmWhatsAppStatusOut(
            status=result.status,
            connected_phone=result.connected_phone,
            qr_code_base64=result.qr_code_base64,
            raw=result.raw,
        )
    except (WhatsAppProviderError, httpx.HTTPError) as exc:
        connection.status = "error"
        connection.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/whatsapp/qrcode", response_model=CrmWhatsAppStatusOut, dependencies=[Depends(require_whatsapp_module)])
async def get_crm_whatsapp_qrcode(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="WhatsApp connection is not configured")
    try:
        result = await get_provider(connection).get_qrcode(connection)
        connection.status = result.status
        connection.connected_phone = result.connected_phone
        connection.qr_code_base64 = result.qr_code_base64
        connection.last_error = None
        db.commit()
        return CrmWhatsAppStatusOut(
            status=result.status,
            connected_phone=result.connected_phone,
            qr_code_base64=result.qr_code_base64,
            raw=result.raw,
        )
    except (WhatsAppProviderError, httpx.HTTPError) as exc:
        connection.status = "error"
        connection.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/whatsapp/disconnect", response_model=dict, dependencies=[Depends(require_whatsapp_module)])
async def disconnect_crm_whatsapp(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="WhatsApp connection is not configured")
    try:
        await get_provider(connection).disconnect(connection)
        connection.status = "disconnected"
        connection.connected_phone = None
        connection.qr_code_base64 = None
        connection.last_error = None
        db.commit()
        return {"status": "disconnected"}
    except (WhatsAppProviderError, httpx.HTTPError) as exc:
        connection.status = "error"
        connection.last_error = str(exc)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@protected.get("/dashboard", response_model=CrmDashboardOut)
def crm_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant),
):
    today_start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    return CrmDashboardOut(
        total_leads=_safe_count(db.query(CrmLead).filter(CrmLead.tenant_id == tenant.id)),
        new_leads=_safe_count(db.query(CrmLead).filter(CrmLead.tenant_id == tenant.id, CrmLead.status == "Novo lead")),
        open_conversations=_safe_count(db.query(CrmConversation).filter(CrmConversation.tenant_id == tenant.id, CrmConversation.status != "resolved")),
        today_followups=_safe_count(
            db.query(CrmFollowUp).filter(
                CrmFollowUp.tenant_id == tenant.id,
                CrmFollowUp.due_at >= today_start,
                CrmFollowUp.due_at < today_end,
                CrmFollowUp.status != "feito",
            )
        ),
        active_conversations=_safe_count(
            db.query(CrmConversation).filter(
                CrmConversation.tenant_id == tenant.id,
                CrmConversation.last_message_at.is_not(None),
            )
        ),
        closed_won=_safe_count(db.query(CrmLead).filter(CrmLead.tenant_id == tenant.id, CrmLead.status == "Fechado")),
        messages_used_month=get_messages_used_month(db, tenant.id),
        current_plan=tenant.plan,
    )


@protected.get("/leads", response_model=list[CrmLeadOut])
def list_crm_leads(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    origin: str | None = Query(default=None),
    responsible_user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CrmLead).filter(CrmLead.tenant_id == current_user.tenant_id)
    if q:
        like = f"%{q}%"
        query = query.filter((CrmLead.name.ilike(like)) | (CrmLead.phone.ilike(like)) | (CrmLead.email.ilike(like)))
    if status_filter:
        query = query.filter(CrmLead.status == status_filter)
    if origin:
        query = query.filter(CrmLead.origin == origin)
    if responsible_user_id:
        query = query.filter(CrmLead.responsible_user_id == responsible_user_id)
    try:
        leads = query.order_by(CrmLead.updated_at.desc()).all()
    except SQLAlchemyError:
        return []
    tags_map = get_lead_tags(db, current_user.tenant_id, [lead.id for lead in leads])
    return [serialize_lead(lead, tags_map.get(lead.id, [])) for lead in leads]


@protected.post("/leads", response_model=CrmLeadOut, status_code=status.HTTP_201_CREATED)
def create_crm_lead(
    payload: CrmLeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = ensure_crm_lead(
        db,
        current_user.tenant_id,
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        origin=payload.origin,
        notes=payload.notes,
    )
    lead.status = payload.status
    lead.responsible_user_id = payload.responsible_user_id
    replace_lead_tags(db, current_user.tenant_id, lead.id, payload.tag_ids)
    log_crm_activity(db, current_user.tenant_id, "lead.saved", "Lead salvo via CRM", lead_id=lead.id)
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead, get_lead_tags(db, current_user.tenant_id, [lead.id]).get(lead.id, []))


@protected.get("/leads/{lead_id}", response_model=CrmLeadOut)
def get_crm_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(CrmLead).filter(CrmLead.id == lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return serialize_lead(lead, get_lead_tags(db, current_user.tenant_id, [lead.id]).get(lead.id, []))


@protected.get("/leads/{lead_id}/activity", response_model=list[CrmActivityLogOut])
def get_crm_lead_activity(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(CrmLead).filter(CrmLead.id == lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db.query(CrmActivityLog).filter(CrmActivityLog.tenant_id == current_user.tenant_id, CrmActivityLog.lead_id == lead.id).order_by(CrmActivityLog.created_at.desc()).all()


@protected.put("/leads/{lead_id}", response_model=CrmLeadOut)
def update_crm_lead(
    lead_id: int,
    payload: CrmLeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(CrmLead).filter(CrmLead.id == lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in payload.model_dump(exclude_unset=True, exclude={"tag_ids"}).items():
        setattr(lead, field, value)
    if payload.tag_ids is not None:
        replace_lead_tags(db, current_user.tenant_id, lead.id, payload.tag_ids)
    log_crm_activity(db, current_user.tenant_id, "lead.updated", "Lead atualizado", lead_id=lead.id)
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead, get_lead_tags(db, current_user.tenant_id, [lead.id]).get(lead.id, []))


@protected.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crm_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(CrmLead).filter(CrmLead.id == lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()


@protected.get("/conversations", response_model=list[CrmConversationOut])
def list_crm_conversations(
    channel: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CrmConversation).filter(CrmConversation.tenant_id == current_user.tenant_id)
    if channel:
        query = query.filter(CrmConversation.channel == channel)
    if status_filter:
        query = query.filter(CrmConversation.status == status_filter)
    return query.order_by(CrmConversation.last_message_at.desc().nullslast(), CrmConversation.updated_at.desc()).all()


@protected.get("/conversations/{conversation_id}", response_model=CrmConversationOut)
def get_crm_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(CrmConversation).filter(CrmConversation.id == conversation_id, CrmConversation.tenant_id == current_user.tenant_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@protected.put("/conversations/{conversation_id}/state", response_model=CrmConversationOut)
def update_crm_conversation_state(
    conversation_id: int,
    payload: CrmConversationStateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(CrmConversation).filter(CrmConversation.id == conversation_id, CrmConversation.tenant_id == current_user.tenant_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    chat = db.query(Chat).filter(Chat.id == conversation.chat_id, Chat.tenant_id == current_user.tenant_id).first() if conversation.chat_id else None
    if payload.assigned_user_id is not None:
        assignee = db.query(User).filter(User.id == payload.assigned_user_id, User.tenant_id == current_user.tenant_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="User not found")
        conversation.assigned_user_id = assignee.id
        if chat:
            chat.assigned_user_id = assignee.id
            chat.status = "human"
    if payload.ai_enabled is not None:
        conversation.ai_enabled = payload.ai_enabled
        if chat:
            chat.ai_paused = not payload.ai_enabled
    if payload.status is not None:
        conversation.status = payload.status
        if chat:
            chat.status = payload.status
    log_crm_activity(db, current_user.tenant_id, "conversation.updated", "Estado da conversa atualizado", lead_id=conversation.lead_id, conversation_id=conversation.id, metadata=payload.model_dump(exclude_none=True))
    db.commit()
    db.refresh(conversation)
    return conversation


@protected.get("/messages", response_model=list[CrmMessageOut])
def list_crm_messages(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(CrmConversation).filter(CrmConversation.id == conversation_id, CrmConversation.tenant_id == current_user.tenant_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.query(CrmMessage).filter(CrmMessage.tenant_id == current_user.tenant_id, CrmMessage.conversation_id == conversation.id).order_by(CrmMessage.created_at.asc()).all()


@protected.post("/conversations/{conversation_id}/messages", response_model=CrmMessageOut, status_code=status.HTTP_201_CREATED)
async def send_crm_conversation_message(
    conversation_id: int,
    payload: CrmConversationMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(CrmConversation).filter(CrmConversation.id == conversation_id, CrmConversation.tenant_id == current_user.tenant_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    chat = db.query(Chat).filter(Chat.id == conversation.chat_id, Chat.tenant_id == current_user.tenant_id).first() if conversation.chat_id else None
    if not chat:
        raise HTTPException(status_code=400, detail="Conversation is not linked to an active chat")
    credit = db.query(Credit).filter(Credit.tenant_id == current_user.tenant_id).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credits not configured")
    if credit.remaining <= 0:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="No credits remaining")

    message = Message(tenant_id=current_user.tenant_id, chat_id=chat.id, sender_type="human", content=payload.content)
    db.add(message)
    chat.last_message = payload.content
    chat.last_message_at = _utcnow()
    chat.status = "human"
    db.flush()

    crm_message = sync_crm_message(db, current_user.tenant_id, conversation, message, conversation.channel)
    conversation.last_message = payload.content
    conversation.last_message_at = message.created_at
    conversation.status = "human"
    credit.used += 1
    credit.remaining -= 1
    db.add(UsageLog(tenant_id=current_user.tenant_id, message_id=message.id, tokens_used=0))
    log_crm_activity(db, current_user.tenant_id, "conversation.message_sent", "Mensagem enviada manualmente pelo CRM", lead_id=conversation.lead_id, conversation_id=conversation.id)
    db.commit()
    db.refresh(crm_message)

    if conversation.channel == "telegram":
        await send_telegram_message(chat.chat_external_id, payload.content)
    elif conversation.channel == "whatsapp":
        connection = db.query(CrmWhatsAppConnection).filter(CrmWhatsAppConnection.tenant_id == current_user.tenant_id).first()
        if not connection:
            raise HTTPException(status_code=404, detail="WhatsApp connection is not configured")
        try:
            await get_provider(connection).send_text(connection, chat.chat_external_id, payload.content)
        except (WhatsAppProviderError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    return crm_message


@protected.get("/kanban", response_model=CrmKanbanBoardOut)
def crm_kanban(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_kanban_module),
):
    try:
        columns = (
            db.query(CrmKanbanColumn)
            .filter(CrmKanbanColumn.tenant_id == current_user.tenant_id)
            .order_by(CrmKanbanColumn.position.asc())
            .all()
        )
    except SQLAlchemyError:
        columns = []
    try:
        leads = db.query(CrmLead).filter(CrmLead.tenant_id == current_user.tenant_id).order_by(CrmLead.updated_at.desc()).all()
    except SQLAlchemyError:
        leads = []
    tags_map = get_lead_tags(db, current_user.tenant_id, [lead.id for lead in leads])
    lead_ids = [lead.id for lead in leads]
    try:
        conversations = (
            db.query(CrmConversation)
            .filter(CrmConversation.tenant_id == current_user.tenant_id, CrmConversation.lead_id.in_(lead_ids))
            .all()
            if lead_ids
            else []
        )
    except SQLAlchemyError:
        conversations = []
    conversation_map = {conversation.lead_id: conversation for conversation in conversations if conversation.lead_id}
    cards: dict[str, list[CrmKanbanCardOut]] = {column.name: [] for column in columns}
    for lead in leads:
        key = lead.status if lead.status in cards else (columns[0].name if columns else lead.status)
        cards.setdefault(key, []).append(CrmKanbanCardOut(lead=serialize_lead(lead, tags_map.get(lead.id, [])), conversation=conversation_map.get(lead.id)))
    return CrmKanbanBoardOut(columns=[CrmKanbanColumnOut.model_validate(column) for column in columns], cards=cards)


@protected.post("/kanban", response_model=CrmKanbanColumnOut, status_code=status.HTTP_201_CREATED)
def create_kanban_column(
    payload: CrmKanbanColumnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_kanban_module),
):
    existing = db.query(CrmKanbanColumn).filter(
        CrmKanbanColumn.tenant_id == current_user.tenant_id,
        CrmKanbanColumn.name == payload.name,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Kanban column already exists")

    column = CrmKanbanColumn(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        color=payload.color,
        position=payload.position,
        is_default=False,
    )
    db.add(column)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(CrmKanbanColumn).filter(
            CrmKanbanColumn.tenant_id == current_user.tenant_id,
            CrmKanbanColumn.name == payload.name,
        ).first()
        if existing:
            return existing
        raise
    db.refresh(column)
    return column


@protected.post("/kanban/move", response_model=CrmLeadOut)
def move_kanban_card(
    payload: CrmKanbanMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: object = Depends(require_kanban_module),
):
    lead = db.query(CrmLead).filter(CrmLead.id == payload.lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    column = db.query(CrmKanbanColumn).filter(CrmKanbanColumn.tenant_id == current_user.tenant_id, CrmKanbanColumn.name == payload.status).first()
    if not column:
        raise HTTPException(status_code=404, detail="Kanban column not found")
    lead.status = column.name
    log_crm_activity(db, current_user.tenant_id, "kanban.moved", f"Lead movido para {column.name}", lead_id=lead.id, metadata={"status": column.name})
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead, get_lead_tags(db, current_user.tenant_id, [lead.id]).get(lead.id, []))


@protected.get("/followups", response_model=list[CrmFollowUpOut])
def list_followups(
    only_today: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CrmFollowUp).filter(CrmFollowUp.tenant_id == current_user.tenant_id)
    if only_today:
        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(CrmFollowUp.due_at >= start, CrmFollowUp.due_at < start + timedelta(days=1))
    return query.order_by(CrmFollowUp.due_at.asc()).all()


@protected.post("/followups", response_model=CrmFollowUpOut, status_code=status.HTTP_201_CREATED)
def create_followup(
    payload: CrmFollowUpCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = db.query(CrmLead).filter(CrmLead.id == payload.lead_id, CrmLead.tenant_id == current_user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    followup = CrmFollowUp(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(followup)
    log_crm_activity(db, current_user.tenant_id, "followup.created", payload.title, lead_id=lead.id)
    db.commit()
    db.refresh(followup)
    return followup


@protected.put("/followups/{followup_id}", response_model=CrmFollowUpOut)
def update_followup(
    followup_id: int,
    payload: CrmFollowUpUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    followup = db.query(CrmFollowUp).filter(CrmFollowUp.id == followup_id, CrmFollowUp.tenant_id == current_user.tenant_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(followup, field, value)
    log_crm_activity(db, current_user.tenant_id, "followup.updated", followup.title, lead_id=followup.lead_id)
    db.commit()
    db.refresh(followup)
    return followup


@protected.delete("/followups/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_followup(followup_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    followup = db.query(CrmFollowUp).filter(CrmFollowUp.id == followup_id, CrmFollowUp.tenant_id == current_user.tenant_id).first()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    log_crm_activity(db, current_user.tenant_id, "followup.deleted", followup.title, lead_id=followup.lead_id)
    db.delete(followup)
    db.commit()


@protected.get("/tasks", response_model=list[CrmTaskOut])
def list_crm_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CrmTask).filter(CrmTask.tenant_id == current_user.tenant_id).order_by(CrmTask.created_at.desc()).all()


@protected.post("/tasks", response_model=CrmTaskOut, status_code=status.HTTP_201_CREATED)
def create_crm_task(
    payload: CrmTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.lead_id is not None and not db.query(CrmLead).filter(CrmLead.id == payload.lead_id, CrmLead.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=404, detail="Lead not found")
    task = CrmTask(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(task)
    log_crm_activity(db, current_user.tenant_id, "task.created", payload.title, lead_id=payload.lead_id)
    db.commit()
    db.refresh(task)
    return task


@protected.put("/tasks/{task_id}", response_model=CrmTaskOut)
def update_crm_task(
    task_id: int,
    payload: CrmTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(CrmTask).filter(CrmTask.id == task_id, CrmTask.tenant_id == current_user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.lead_id is not None and not db.query(CrmLead).filter(CrmLead.id == payload.lead_id, CrmLead.tenant_id == current_user.tenant_id).first():
        raise HTTPException(status_code=404, detail="Lead not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    log_crm_activity(db, current_user.tenant_id, "task.updated", task.title, lead_id=task.lead_id)
    db.commit()
    db.refresh(task)
    return task


@protected.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crm_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(CrmTask).filter(CrmTask.id == task_id, CrmTask.tenant_id == current_user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    log_crm_activity(db, current_user.tenant_id, "task.deleted", task.title, lead_id=task.lead_id)
    db.delete(task)
    db.commit()


@protected.get("/tags", response_model=list[CrmTagOut])
def list_crm_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CrmTag).filter(CrmTag.tenant_id == current_user.tenant_id).order_by(CrmTag.name.asc()).all()


@protected.post("/tags", response_model=CrmTagOut, status_code=status.HTTP_201_CREATED)
def create_crm_tag(payload: CrmTagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.query(CrmTag).filter(CrmTag.tenant_id == current_user.tenant_id, CrmTag.name == payload.name).first()
    if tag:
        return tag
    tag = CrmTag(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@protected.get("/settings", response_model=CrmSettingsOut)
def get_crm_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_crm_defaults(db, current_user.tenant_id)
    db.commit()
    settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == current_user.tenant_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="CRM settings not found")
    return serialize_settings(settings)


@protected.put("/settings", response_model=CrmSettingsOut)
def update_crm_settings(
    payload: CrmSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_crm_defaults(db, current_user.tenant_id)
    settings = db.query(CrmSetting).filter(CrmSetting.tenant_id == current_user.tenant_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="CRM settings not found")

    if payload.status_options is not None:
        from app.services.crm import dumps_json
        settings.status_options_json = dumps_json(payload.status_options)
    if payload.tags is not None:
        from app.services.crm import dumps_json
        settings.tags_json = dumps_json(payload.tags)
    if payload.initial_auto_message is not None:
        settings.initial_auto_message = payload.initial_auto_message
    if payload.business_hours is not None:
        from app.services.crm import dumps_json
        settings.business_hours_json = dumps_json(payload.business_hours)
    if payload.hermes_enabled is not None:
        settings.hermes_enabled = payload.hermes_enabled
    if payload.column_names is not None:
        columns = db.query(CrmKanbanColumn).filter(CrmKanbanColumn.tenant_id == current_user.tenant_id).order_by(CrmKanbanColumn.position.asc()).all()
        for index, name in enumerate(payload.column_names):
            if index < len(columns):
                columns[index].name = name

    db.commit()
    db.refresh(settings)
    return serialize_settings(settings)


router.include_router(protected)
