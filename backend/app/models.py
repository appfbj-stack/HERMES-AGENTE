from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    niche: Mapped[str | None] = mapped_column(String(50), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    bot_display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    telegram_bot_token: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    telegram_bot_username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="agent")
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")

    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="telegram")
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chat_external_id: Mapped[str] = mapped_column(String(255), index=True)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    ai_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("tenant_id", "channel", "chat_external_id", name="uq_chat_external"),)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), index=True)
    sender_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="messages")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interest: Mapped[str | None] = mapped_column(Text, nullable=True)
    origem: Mapped[str] = mapped_column(String(50), default="manual")
    status: Mapped[str] = mapped_column(String(50), default="new")
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kanban_column_id: Mapped[int | None] = mapped_column(ForeignKey("crm_kanban_columns.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AssistantMemory(Base):
    __tablename__ = "assistant_memory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("tenant_id", "key", name="uq_memory_tenant_key"),)


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[int] = mapped_column(Integer, default=0)
    remaining: Mapped[int] = mapped_column(Integer, default=0)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    monthly_credits: Mapped[int] = mapped_column(Integer)
    price_cents: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    asaas_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asaas_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    asaas_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(32))
    value_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    billing_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    invoice_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    pix_qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    pix_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits_added: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TenantModule(Base, TimestampMixin):
    __tablename__ = "tenant_modules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    crm: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)


class CrmLead(Base, TimestampMixin):
    __tablename__ = "crm_leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    origin: Mapped[str] = mapped_column(String(50), default="manual")
    status: Mapped[str] = mapped_column(String(100), default="Novo lead", index=True)
    responsible_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("tenant_id", "phone", name="uq_crm_leads_tenant_phone"),)


class CrmConversation(Base, TimestampMixin):
    __tablename__ = "crm_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("crm_leads.id"), nullable=True, index=True)
    chat_id: Mapped[int | None] = mapped_column(ForeignKey("chats.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(50), default="telegram")
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("tenant_id", "channel", "external_id", name="uq_crm_conversation_external"),)


class CrmMessage(Base, TimestampMixin):
    __tablename__ = "crm_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("crm_conversations.id"), index=True)
    legacy_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True, index=True)
    sender_type: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50), default="telegram")
    content: Mapped[str] = mapped_column(Text)


class CrmKanbanColumn(Base, TimestampMixin):
    __tablename__ = "crm_kanban_columns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_crm_kanban_tenant_name"),)


class CrmFollowUp(Base, TimestampMixin):
    __tablename__ = "crm_followups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("crm_leads.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pendente")
    channel: Mapped[str] = mapped_column(String(50), default="whatsapp")
    responsible_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class CrmTask(Base, TimestampMixin):
    __tablename__ = "crm_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pendente")
    priority: Mapped[str] = mapped_column(String(50), default="media")
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("crm_leads.id"), nullable=True)


class CrmTag(Base, TimestampMixin):
    __tablename__ = "crm_tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_crm_tags_tenant_name"),)


class CrmLeadTag(Base, TimestampMixin):
    __tablename__ = "crm_lead_tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("crm_leads.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("crm_tags.id"), index=True)

    __table_args__ = (UniqueConstraint("tenant_id", "lead_id", "tag_id", name="uq_crm_lead_tag"),)


class CrmActivityLog(Base, TimestampMixin):
    __tablename__ = "crm_activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("crm_leads.id"), nullable=True, index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("crm_conversations.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CrmSetting(Base, TimestampMixin):
    __tablename__ = "crm_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    status_options_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    initial_auto_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_hours_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    hermes_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class CrmWhatsAppConnection(Base, TimestampMixin):
    __tablename__ = "crm_whatsapp_connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="evolution_go")
    instance_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    api_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="disconnected")
    connected_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qr_code_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_webhook_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_webhook_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_webhook_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


CrmFollowup = CrmFollowUp
CrmSettings = CrmSetting


class SkillExecution(Base, TimestampMixin):
    __tablename__ = "skill_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    skill_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminTask(Base, TimestampMixin):
    __tablename__ = "admin_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    related_tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminProject(Base, TimestampMixin):
    __tablename__ = "admin_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AdminRoutine(Base, TimestampMixin):
    __tablename__ = "admin_routines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule_type: Mapped[str] = mapped_column(String(50))
    schedule_value: Mapped[int]
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdminMemory(Base, TimestampMixin):
    __tablename__ = "admin_memory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(100))
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(Text)
    meta_data: Mapped[str | None] = mapped_column(Text, nullable=True)


class AdminActionLog(Base, TimestampMixin):
    __tablename__ = "admin_action_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True)


class AdminSkill(Base, TimestampMixin):
    __tablename__ = "admin_skills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual")
    trigger_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instructions: Mapped[str] = mapped_column(Text)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
