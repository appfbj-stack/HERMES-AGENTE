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


class TenantAdminOut(TenantOut):
    """Visão estendida só pra super admin."""
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


# ===== Billing / Asaas =====
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
    billing_type: str = "PIX"  # PIX | BOLETO | CREDIT_CARD
    cpf_cnpj: str | None = None
    phone: str | None = None


class BuyCreditsRequest(BaseModel):
    credits: int = Field(gt=0)
    value_cents: int = Field(gt=0)
    billing_type: str = "PIX"
    cpf_cnpj: str | None = None


class MeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut


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


# ===== CRM =====

class CrmTagCreate(BaseModel):
    name: str
    color: str = "#10b981"


class CrmTagOut(BaseModel):
    id: int
    tenant_id: int
    name: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True


class CrmKanbanColumnCreate(BaseModel):
    name: str
    color: str = "#6366f1"
    position: int = 0


class CrmKanbanColumnOut(BaseModel):
    id: int
    tenant_id: int
    name: str
    color: str
    position: int
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CrmKanbanMoveRequest(BaseModel):
    lead_id: int
    column_id: int


class CrmFollowupCreate(BaseModel):
    lead_id: int
    titulo: str
    descricao: str | None = None
    data_hora: datetime
    canal: str = "whatsapp"


class CrmFollowupUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    data_hora: datetime | None = None
    status: str | None = None
    canal: str | None = None


class CrmFollowupOut(BaseModel):
    id: int
    tenant_id: int
    lead_id: int
    titulo: str
    descricao: str | None = None
    data_hora: datetime
    status: str
    canal: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CrmActivityLogOut(BaseModel):
    id: int
    lead_id: int
    user_id: int | None = None
    action: str
    detail: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CrmSettingsUpdate(BaseModel):
    mensagem_inicial: str | None = None
    horario_inicio: str | None = None
    horario_fim: str | None = None
    hermes_ativo: bool | None = None
    notificar_followup_telegram: bool | None = None


class CrmSettingsOut(BaseModel):
    tenant_id: int
    mensagem_inicial: str | None = None
    horario_inicio: str
    horario_fim: str
    hermes_ativo: bool
    notificar_followup_telegram: bool
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CrmDashboardOut(BaseModel):
    total_leads: int
    leads_novos: int
    atendimentos_abertos: int
    followups_hoje: int
    conversas_ativas: int
    fechamentos: int
    mensagens_usadas_mes: int
    plano_atual: str
    creditos_restantes: int


class TenantModuleOut(BaseModel):
    tenant_id: int
    crm: bool
    whatsapp: bool

    class Config:
        from_attributes = True


class TenantModuleUpdate(BaseModel):
    crm: bool | None = None
    whatsapp: bool | None = None


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

