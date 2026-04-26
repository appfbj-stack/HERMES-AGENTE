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
    interest: str | None = None
    status: str = "new"


class LeadOut(LeadCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    status: str = "pending"


class TaskOut(TaskCreate):
    id: int
    created_at: datetime

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

