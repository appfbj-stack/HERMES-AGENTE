from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class BootstrapRequest(BaseModel):
    token: str
    tenant_name: str
    tenant_email: EmailStr
    user_name: str
    user_email: EmailStr
    password: str = Field(min_length=6)
    plan: str = "pro"
    credits: int = 500


class UserOut(BaseModel):
    id: int
    tenant_id: int
    name: str
    email: EmailStr
    role: str
    is_super_admin: bool = False

    class Config:
        from_attributes = True


class TenantOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    plan: str
    active: bool
    niche: str | None = None
    system_prompt: str | None = None
    bot_display_name: str | None = None
    welcome_message: str | None = None
    telegram_bot_username: str | None = None

    class Config:
        from_attributes = True


class TenantModulesOut(BaseModel):
    crm: bool
    whatsapp: bool = False


class MeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut
    modules: TenantModulesOut


class TenantAdminOut(TenantOut):
    telegram_bot_token: str | None = None
    created_at: datetime
    credits_total: int = 0
    credits_used: int = 0
    credits_remaining: int = 0
    crm_enabled: bool = False

    class Config:
        from_attributes = True


class TenantCreateAdmin(BaseModel):
    name: str
    email: EmailStr
    plan: str = "starter"
    niche: str | None = None
    system_prompt: str | None = None
    bot_display_name: str | None = None
    welcome_message: str | None = None
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None
    credits: int = 1000
    user_name: str
    user_email: EmailStr
    user_password: str = Field(min_length=6)


class TenantUpdateAdmin(BaseModel):
    name: str | None = None
    plan: str | None = None
    active: bool | None = None
    niche: str | None = None
    system_prompt: str | None = None
    bot_display_name: str | None = None
    welcome_message: str | None = None
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None


class CreditsAddRequest(BaseModel):
    amount: int = Field(gt=0)


class PlanOut(BaseModel):
    id: int
    code: str
    name: str
    monthly_credits: int
    price_cents: int
    description: str | None = None

    class Config:
        from_attributes = True


class SubscriptionOut(BaseModel):
    id: int
    plan_id: int
    plan: PlanOut | None = None
    status: str
    next_due_date: datetime | None = None
    last_paid_at: datetime | None = None
    asaas_subscription_id: str | None = None

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    id: int
    type: str
    value_cents: int
    status: str
    billing_type: str | None
    invoice_url: str | None
    pix_qr_code: str | None
    pix_payload: str | None
    credits_added: int
    due_date: datetime | None
    paid_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    plan_id: int
    billing_type: str = "PIX"
    cpf_cnpj: str | None = None
    phone: str | None = None


class BuyCreditsRequest(BaseModel):
    credits: int = Field(gt=0)
    value_cents: int = Field(gt=0)
    billing_type: str = "PIX"
    cpf_cnpj: str | None = None


class ChatOut(BaseModel):
    id: int
    channel: str
    contact_name: str | None
    contact_phone: str | None
    chat_external_id: str
    last_message: str | None
    last_message_at: datetime | None
    status: str
    ai_paused: bool
    assigned_user_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class LeadCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    interest: str | None = None
    origem: str = "manual"
    status: str = "new"
    responsavel_id: int | None = None
    observacoes: str | None = None
    kanban_column_id: int | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    interest: str | None = None
    origem: str | None = None
    status: str | None = None
    responsavel_id: int | None = None
    observacoes: str | None = None
    kanban_column_id: int | None = None
    last_contact_at: datetime | None = None


class LeadOut(BaseModel):
    id: int
    tenant_id: int
    name: str
    phone: str | None = None
    email: str | None = None
    interest: str | None = None
    origem: str = "manual"
    status: str = "new"
    responsavel_id: int | None = None
    observacoes: str | None = None
    kanban_column_id: int | None = None
    last_contact_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    status: str = "pending"
    priority: str = "normal"
    lead_id: int | None = None
    assigned_user_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    status: str | None = None
    priority: str | None = None
    lead_id: int | None = None
    assigned_user_id: int | None = None


class TaskOut(BaseModel):
    id: int
    tenant_id: int
    title: str
    description: str | None = None
    due_date: datetime | None = None
    status: str = "pending"
    priority: str = "normal"
    lead_id: int | None = None
    assigned_user_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CreditOut(BaseModel):
    total: int
    used: int
    remaining: int

    class Config:
        from_attributes = True


class AssignChatRequest(BaseModel):
    assigned_user_id: int


class ToggleAIRequest(BaseModel):
    ai_paused: bool


class CrmTagCreate(BaseModel):
    name: str
    color: str | None = None


class CrmTagOut(CrmTagCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmLeadBase(BaseModel):
    name: str
    phone: str | None = None
    email: EmailStr | None = None
    origin: str = "manual"
    status: str = "Novo lead"
    responsible_user_id: int | None = None
    notes: str | None = None
    tag_ids: list[int] = []


class CrmLeadCreate(CrmLeadBase):
    pass


class CrmLeadUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    origin: str | None = None
    status: str | None = None
    responsible_user_id: int | None = None
    notes: str | None = None
    tag_ids: list[int] | None = None


class CrmLeadOut(BaseModel):
    id: int
    tenant_id: int
    name: str
    phone: str | None
    email: EmailStr | None
    origin: str
    status: str
    responsible_user_id: int | None
    notes: str | None
    last_contact_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[CrmTagOut] = []

    class Config:
        from_attributes = True


class CrmConversationOut(BaseModel):
    id: int
    lead_id: int | None
    chat_id: int | None
    channel: str
    external_id: str
    contact_name: str | None
    contact_phone: str | None
    status: str
    ai_enabled: bool
    assigned_user_id: int | None
    last_message: str | None
    last_message_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmConversationStateUpdate(BaseModel):
    assigned_user_id: int | None = None
    ai_enabled: bool | None = None
    status: str | None = None


class CrmConversationMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class CrmMessageOut(BaseModel):
    id: int
    conversation_id: int
    legacy_message_id: int | None
    sender_type: str
    channel: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmActivityLogOut(BaseModel):
    id: int
    tenant_id: int
    lead_id: int | None
    conversation_id: int | None
    action: str
    description: str | None
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmKanbanColumnOut(BaseModel):
    id: int
    name: str
    position: int
    color: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmKanbanCardOut(BaseModel):
    lead: CrmLeadOut
    conversation: CrmConversationOut | None = None


class CrmKanbanBoardOut(BaseModel):
    columns: list[CrmKanbanColumnOut]
    cards: dict[str, list[CrmKanbanCardOut]]


class CrmKanbanMoveRequest(BaseModel):
    lead_id: int
    status: str


class CrmFollowUpCreate(BaseModel):
    lead_id: int
    title: str
    description: str | None = None
    due_at: datetime
    status: str = "pendente"
    channel: str = "whatsapp"
    responsible_user_id: int | None = None


class CrmFollowUpUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    status: str | None = None
    channel: str | None = None
    responsible_user_id: int | None = None


class CrmFollowUpOut(CrmFollowUpCreate):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmTaskCreate(BaseModel):
    title: str
    description: str | None = None
    responsible_user_id: int | None = None
    due_at: datetime | None = None
    status: str = "pendente"
    priority: str = "media"
    lead_id: int | None = None


class CrmTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    responsible_user_id: int | None = None
    due_at: datetime | None = None
    status: str | None = None
    priority: str | None = None
    lead_id: int | None = None


class CrmTaskOut(CrmTaskCreate):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmSettingsUpdate(BaseModel):
    column_names: list[str] | None = None
    status_options: list[str] | None = None
    tags: list[str] | None = None
    initial_auto_message: str | None = None
    business_hours: dict | None = None
    hermes_enabled: bool | None = None


class CrmSettingsOut(BaseModel):
    id: int
    tenant_id: int
    status_options: list[str]
    tags: list[str]
    initial_auto_message: str | None
    business_hours: dict
    hermes_enabled: bool
    created_at: datetime
    updated_at: datetime


class CrmDashboardOut(BaseModel):
    total_leads: int
    new_leads: int
    open_conversations: int
    today_followups: int
    active_conversations: int
    closed_won: int
    messages_used_month: int
    current_plan: str


class CrmModuleUpdate(BaseModel):
    crm: bool


class TenantModuleUpdate(BaseModel):
    crm: bool | None = None
    whatsapp: bool | None = None


class CrmWhatsAppConnectionUpsert(BaseModel):
    provider: str = "evolution_go"
    instance_name: str
    api_base_url: str | None = None
    api_key: str | None = None
    webhook_url: str | None = None


class CrmWhatsAppConnectionOut(BaseModel):
    id: int
    tenant_id: int
    provider: str
    instance_name: str
    api_base_url: str | None
    webhook_url: str | None
    status: str
    connected_phone: str | None
    qr_code_base64: str | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrmWhatsAppStatusOut(BaseModel):
    status: str
    connected_phone: str | None = None
    qr_code_base64: str | None = None
    raw: dict | list | None = None
