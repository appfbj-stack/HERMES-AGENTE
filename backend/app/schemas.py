from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_email: EmailStr | None = None

    @field_validator("tenant_email", mode="before")
    @classmethod
    def empty_tenant_email_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class BootstrapRequest(BaseModel):
    token: str
    tenant_name: str
    tenant_email: EmailStr
    user_name: str
    user_email: EmailStr
    password: str = Field(min_length=6)
    plan: str = "pro"
    credits: int = 500


class AdminSeedSyncRequest(BaseModel):
    token: str


class UserOut(ORMModel):
    id: int
    tenant_id: int
    name: str
    email: EmailStr
    role: str
    is_super_admin: bool = False

class TenantOut(ORMModel):
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

class TenantModulesOut(BaseModel):
    crm: bool
    whatsapp: bool = False
    kanban: bool = False
    agenda: bool = False
    instagram: bool = False
    youtube: bool = False
    content_publisher: bool = False


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
    whatsapp_enabled: bool = False
    kanban_enabled: bool = False
    agenda_enabled: bool = False
    instagram_enabled: bool = False
    youtube_enabled: bool = False
    content_publisher_enabled: bool = False

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


class PlanOut(ORMModel):
    id: int
    code: str
    name: str
    monthly_credits: int
    price_cents: int
    description: str | None = None

class SubscriptionOut(ORMModel):
    id: int
    plan_id: int
    plan: PlanOut | None = None
    status: str
    next_due_date: datetime | None = None
    last_paid_at: datetime | None = None
    asaas_subscription_id: str | None = None

class PaymentOut(ORMModel):
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


class ChatOut(ORMModel):
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

class MessageOut(ORMModel):
    id: int
    chat_id: int
    sender_type: str
    content: str
    created_at: datetime

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


class LeadOut(ORMModel):
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


class TaskOut(ORMModel):
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

class CreditOut(ORMModel):
    total: int
    used: int
    remaining: int


class ClientProfileOut(ORMModel):
    tenant_id: int
    tipo_negocio: str | None = None
    objetivo: str | None = None
    horario_funcionamento: str | None = None
    preferencias: str | None = None
    nivel_automacao: str = "medio"
    created_at: datetime
    updated_at: datetime


class ClientProfileUpdate(BaseModel):
    tipo_negocio: str | None = None
    objetivo: str | None = None
    horario_funcionamento: str | None = None
    preferencias: str | None = None
    nivel_automacao: str | None = None


class ClientSkillOut(ORMModel):
    id: int
    tenant_id: int
    nome_skill: str
    descricao: str | None = None
    ativa: bool = False
    configuracao: str | None = None
    created_at: datetime
    updated_at: datetime


class ClientSkillCreate(BaseModel):
    nome_skill: str
    descricao: str | None = None
    ativa: bool = False
    configuracao: str | None = None


class ClientSkillToggleRequest(BaseModel):
    ativa: bool


class ClientSkillActivationRequest(BaseModel):
    skill_key: str


class ClientSuggestionOut(BaseModel):
    skill_key: str
    message: str
    suggested_at: str | None = None
    active: bool = False

class AssignChatRequest(BaseModel):
    assigned_user_id: int


class ToggleAIRequest(BaseModel):
    ai_paused: bool


class CrmTagCreate(BaseModel):
    name: str
    color: str | None = None


class CrmTagOut(CrmTagCreate, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime

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


class CrmLeadOut(ORMModel):
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

class CrmConversationOut(ORMModel):
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

class CrmConversationStateUpdate(BaseModel):
    assigned_user_id: int | None = None
    ai_enabled: bool | None = None
    status: str | None = None


class CrmConversationMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class CrmMessageOut(ORMModel):
    id: int
    conversation_id: int
    legacy_message_id: int | None
    sender_type: str
    channel: str
    content: str
    created_at: datetime
    updated_at: datetime

class CrmActivityLogOut(ORMModel):
    id: int
    tenant_id: int
    lead_id: int | None
    conversation_id: int | None
    action: str
    description: str | None
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime

class CrmKanbanColumnOut(ORMModel):
    id: int
    name: str
    position: int
    color: str | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

class CrmKanbanColumnCreate(BaseModel):
    name: str
    color: str | None = None
    position: int = 0


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


class CrmFollowUpOut(CrmFollowUpCreate, ORMModel):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

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


class CrmTaskOut(CrmTaskCreate, ORMModel):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

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
    kanban: bool | None = None
    agenda: bool | None = None
    instagram: bool | None = None
    youtube: bool | None = None
    content_publisher: bool | None = None


class CrmWhatsAppConnectionUpsert(BaseModel):
    provider: str = "evolution_go"
    instance_name: str
    api_base_url: str | None = None
    api_key: str | None = None
    webhook_url: str | None = None


class CrmWhatsAppConnectionOut(ORMModel):
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
    last_webhook_event: str | None = None
    last_webhook_payload: str | None = None
    last_webhook_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

class CrmWhatsAppStatusOut(BaseModel):
    status: str
    connected_phone: str | None = None
    qr_code_base64: str | None = None
    raw: dict | list | None = None


class GitHubCommitRequest(BaseModel):
    message: str = Field(min_length=1)
    files: list[str] | None = None
    author_name: str | None = None
    author_email: str | None = None


class GitHubPushRequest(BaseModel):
    branch: str = "main"


class GitHubPullRequestRequest(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    head: str = Field(min_length=1)
    base: str = "main"


class FileListRequest(BaseModel):
    path: str = "./"
    pattern: str | None = None


class FileReadRequest(BaseModel):
    path: str = Field(min_length=1)
    encoding: str = "utf-8"


class FileWriteRequest(BaseModel):
    path: str = Field(min_length=1)
    content: str
    encoding: str = "utf-8"
    create_dirs: bool = True


class FileDeleteRequest(BaseModel):
    path: str = Field(min_length=1)


class CoolifyDeployRequest(BaseModel):
    application_id: str = Field(min_length=1)
    branch: str | None = None
    force_rebuild: bool = False


class CoolifyTriggerRequest(BaseModel):
    webhook_url: str = Field(min_length=1)
    payload: dict | None = None


class CoolifyStatusRequest(BaseModel):
    application_id: str = Field(min_length=1)


class CoolifyDeploymentsRequest(BaseModel):
    application_id: str = Field(min_length=1)
    limit: int = 10


class SocialFileListRequest(BaseModel):
    pattern: str | None = None
    subfolder: str | None = None


class SocialFileReadRequest(BaseModel):
    filename: str = Field(min_length=1)
    subfolder: str | None = None
    encoding: str = "utf-8"


class SocialFileWriteRequest(BaseModel):
    filename: str = Field(min_length=1)
    content: str
    subfolder: str | None = None
    encoding: str = "utf-8"


class SocialFileDeleteRequest(BaseModel):
    filename: str = Field(min_length=1)
    subfolder: str | None = None


class RoutineExecuteRequest(BaseModel):
    routine_name: str = Field(min_length=1)
    input_data: str | None = None


class RoutineScheduleRequest(BaseModel):
    routine_name: str = Field(min_length=1)
    interval: str = Field(min_length=1)
    interval_value: int = Field(gt=0)


class RoutineCancelRequest(BaseModel):
    job_id: str = Field(min_length=1)


class SkillExecutionOut(ORMModel):
    id: int
    tenant_id: int
    skill_name: str
    status: str
    input_data: str | None
    output_data: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

class SkillExecutionsListOut(BaseModel):
    executions: list[SkillExecutionOut]
    total: int


class HermesAdminChatRequest(BaseModel):
    message: str = Field(min_length=1)


class HermesAdminChatResponse(BaseModel):
    response: str
    actions: list[str] = []
    context: dict = {}


class AdminTaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    priority: str = "normal"
    assigned_user_id: int | None = None
    related_tenant_id: int | None = None
    due_date: datetime | None = None


class AdminTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_user_id: int | None = None
    due_date: datetime | None = None


class AdminTaskOut(ORMModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    assigned_user_id: int | None
    related_tenant_id: int | None
    due_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

class AdminTaskListOut(BaseModel):
    tasks: list[AdminTaskOut]
    total: int


class AdminProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    priority: str = "normal"
    due_date: datetime | None = None


class AdminProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class AdminProjectOut(ORMModel):
    id: int
    name: str
    description: str | None
    status: str
    priority: str
    due_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

class AdminProjectListOut(BaseModel):
    projects: list[AdminProjectOut]
    total: int


class AdminRoutineCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    schedule_type: str = Field(min_length=1)
    schedule_value: int = Field(gt=0)


class AdminRoutineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    schedule_type: str | None = None
    schedule_value: int | None = None
    is_active: bool | None = None


class AdminRoutineOut(ORMModel):
    id: int
    name: str
    description: str | None
    schedule_type: str
    schedule_value: int
    last_run_at: datetime | None
    next_run_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

class AdminRoutineListOut(BaseModel):
    routines: list[AdminRoutineOut]
    total: int


class AdminMemoryCreate(BaseModel):
    category: str = Field(min_length=1)
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    meta_data: str | None = None


class AdminMemoryUpdate(BaseModel):
    category: str | None = None
    key: str | None = None
    value: str | None = None
    meta_data: str | None = None


class AdminMemoryOut(ORMModel):
    id: int
    category: str
    key: str
    value: str
    meta_data: str | None
    created_at: datetime
    updated_at: datetime

class AdminMemoryListOut(BaseModel):
    memories: list[AdminMemoryOut]
    total: int


class AdminActionLogOut(ORMModel):
    id: int
    action: str
    entity_type: str
    entity_id: int | None
    details: str | None
    performed_by_user_id: int | None
    tenant_id: int | None
    created_at: datetime

class AdminActionLogListOut(BaseModel):
    logs: list[AdminActionLogOut]
    total: int


class HermesAdminDashboardOut(BaseModel):
    active_tenants: int
    blocked_tenants: int
    pending_payments: int
    messages_used_month: int
    open_tasks: int
    active_projects: int
    active_routines: int
    total_revenue: float



class AdminSkillCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    trigger_type: str = 'manual'
    trigger_value: str | None = None
    instructions: str = Field(min_length=1)
    expected_result: str | None = None
    active: bool = True


class AdminSkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    trigger_value: str | None = None
    instructions: str | None = None
    expected_result: str | None = None
    active: bool | None = None


class AdminSkillOut(ORMModel):
    id: int
    name: str
    description: str | None
    trigger_type: str
    trigger_value: str | None
    instructions: str
    expected_result: str | None
    active: bool
    last_run_at: datetime | None
    last_run_result: str | None
    last_run_status: str | None
    created_at: datetime
    updated_at: datetime

class AdminSkillListOut(BaseModel):
    skills: list[AdminSkillOut]
    total: int


class AdminSkillRunRequest(BaseModel):
    parameters: dict | None = None


class AdminSkillRunResponse(BaseModel):
    skill_id: int
    skill_name: str
    status: str
    result: str | None
    error: str | None
    execution_time: float
    executed_at: datetime


class SkillSuggestionResponse(BaseModel):
    suggestion: AdminSkillCreate
    confidence: float
    reason: str
