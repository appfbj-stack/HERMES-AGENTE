from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.middleware import (
    global_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.routes.admin import router as admin_router
from app.routes.admin_hermes import router as admin_hermes_router
from app.routes.auth import router as auth_router
from app.routes.billing import router as billing_router
from app.routes.chats import router as chats_router
from app.routes.credits import router as credits_router
from app.routes.crm import router as crm_router
from app.routes.health import router as health_router
from app.routes.integrations import router as integrations_router
from app.routes.leads import router as leads_router
from app.routes.messages import router as messages_router
from app.routes.public import router as public_router
from app.routes.tasks import router as tasks_router
from app.routes.tools import router as tools_router
from app.routes.webhook import router as webhook_router

settings = get_settings()

setup_logging(settings.log_level)

app = FastAPI(title="Hermes Agente API", version="0.2.0")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Migrações leves (idempotentes) — adicionam colunas novas em DBs existentes.
MIGRATIONS = [
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS niche VARCHAR(50)",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS system_prompt TEXT",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS telegram_bot_token VARCHAR(255)",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS telegram_bot_username VARCHAR(100)",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS bot_display_name VARCHAR(80)",
    "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS welcome_message TEXT",
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_telegram_bot_token ON tenants(telegram_bot_token) WHERE telegram_bot_token IS NOT NULL",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN NOT NULL DEFAULT FALSE",
    # Promove o primeiro usuário a super admin (idempotente)
    "UPDATE users SET is_super_admin = TRUE WHERE id = (SELECT id FROM users ORDER BY id ASC LIMIT 1) AND is_super_admin = FALSE",
    # ===== CRM — chat.lead_id =====
    "ALTER TABLE chats ADD COLUMN IF NOT EXISTS lead_id INTEGER REFERENCES leads(id)",
    # ===== CRM — novos campos em leads =====
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS origem VARCHAR(50) NOT NULL DEFAULT 'manual'",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS responsavel_id INTEGER REFERENCES users(id)",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS observacoes TEXT",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_contact_at TIMESTAMPTZ",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS kanban_column_id INTEGER REFERENCES crm_kanban_columns(id)",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # ===== CRM — novos campos em tasks =====
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'normal'",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS lead_id INTEGER REFERENCES leads(id)",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assigned_user_id INTEGER REFERENCES users(id)",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # ===== TimestampMixin — tabelas criadas antes do mixin ser adicionado =====
    "ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_kanban_columns ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_kanban_columns ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_tags ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_tags ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_lead_tags ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_lead_tags ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_followups ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_followups ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_activity_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_activity_logs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # ===== CRM — colunas de crm_settings (tabela criada antes do schema atual) =====
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS status_options_json TEXT",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS tags_json TEXT",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS initial_auto_message TEXT",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS business_hours_json TEXT",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS hermes_enabled BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()",
    "ALTER TABLE crm_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
    # ===== CRM — colunas de crm_whatsapp_connections =====
    "ALTER TABLE crm_whatsapp_connections ADD COLUMN IF NOT EXISTS last_webhook_event VARCHAR(100)",
    "ALTER TABLE crm_whatsapp_connections ADD COLUMN IF NOT EXISTS last_webhook_payload TEXT",
    "ALTER TABLE crm_whatsapp_connections ADD COLUMN IF NOT EXISTS last_webhook_at TIMESTAMPTZ",
    # ===== Seed de planos default =====
    """INSERT INTO plans (code, name, monthly_credits, price_cents, description, active)
       VALUES ('starter', 'Starter', 1000, 9700, '1.000 mensagens/mês • 1 canal • IA com nicho', true)
       ON CONFLICT (code) DO NOTHING""",
    """INSERT INTO plans (code, name, monthly_credits, price_cents, description, active)
       VALUES ('pro', 'Pro', 5000, 29700, '5.000 mensagens/mês • 3 canais • CRM completo', true)
       ON CONFLICT (code) DO NOTHING""",
    """INSERT INTO plans (code, name, monthly_credits, price_cents, description, active)
       VALUES ('enterprise', 'Enterprise', 20000, 89700, '20.000 mensagens/mês • Canais ilimitados • Bot dedicado • Suporte', true)
       ON CONFLICT (code) DO NOTHING""",
    # ===== CRM Tables (Create if not exists) =====
    """CREATE TABLE IF NOT EXISTS crm_settings (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
        status_options_json TEXT,
        tags_json TEXT,
        initial_auto_message TEXT,
        business_hours_json TEXT,
        hermes_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_kanban_columns (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        position INTEGER NOT NULL,
        color VARCHAR(20),
        is_default BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_tags (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        color VARCHAR(20),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_leads (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(255),
        origin VARCHAR(50) NOT NULL DEFAULT 'manual',
        status VARCHAR(50) NOT NULL DEFAULT 'Novo lead',
        responsible_user_id INTEGER REFERENCES users(id),
        notes TEXT,
        last_contact_at TIMESTAMPTZ,
        kanban_column_id INTEGER REFERENCES crm_kanban_columns(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        CONSTRAINT uq_crm_leads_tenant_phone UNIQUE (tenant_id, phone)
    )""",
    """CREATE TABLE IF NOT EXISTS crm_conversations (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        lead_id INTEGER REFERENCES crm_leads(id) ON DELETE SET NULL,
        chat_id INTEGER REFERENCES chats(id) ON DELETE SET NULL,
        channel VARCHAR(20) NOT NULL,
        external_id VARCHAR(255) NOT NULL,
        contact_name VARCHAR(255),
        contact_phone VARCHAR(20),
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        ai_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        assigned_user_id INTEGER REFERENCES users(id),
        last_message TEXT,
        last_message_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_messages (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        conversation_id INTEGER NOT NULL REFERENCES crm_conversations(id) ON DELETE CASCADE,
        legacy_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
        sender_type VARCHAR(20) NOT NULL,
        channel VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_followups (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        lead_id INTEGER NOT NULL REFERENCES crm_leads(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        due_at TIMESTAMPTZ NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
        channel VARCHAR(20),
        responsible_user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_tasks (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        responsible_user_id INTEGER REFERENCES users(id),
        due_at TIMESTAMPTZ,
        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
        priority VARCHAR(20) NOT NULL DEFAULT 'normal',
        lead_id INTEGER REFERENCES crm_leads(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_lead_tags (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        lead_id INTEGER NOT NULL REFERENCES crm_leads(id) ON DELETE CASCADE,
        tag_id INTEGER NOT NULL REFERENCES crm_tags(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        CONSTRAINT uq_crm_lead_tags_lead_tag UNIQUE (lead_id, tag_id)
    )""",
    """CREATE TABLE IF NOT EXISTS crm_activity_logs (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        lead_id INTEGER NOT NULL REFERENCES crm_leads(id) ON DELETE CASCADE,
        action VARCHAR(100) NOT NULL,
        details TEXT,
        performed_by_user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS crm_whatsapp_connections (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
        provider VARCHAR(50) NOT NULL,
        instance_name VARCHAR(100) NOT NULL,
        api_base_url TEXT,
        api_key TEXT,
        webhook_url TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'disconnected',
        connected_phone VARCHAR(20),
        qr_code_base64 TEXT,
        last_error TEXT,
        last_webhook_event VARCHAR(100),
        last_webhook_payload TEXT,
        last_webhook_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    # ===== CRM Indexes =====
    """CREATE INDEX IF NOT EXISTS ix_crm_settings_tenant_id ON crm_settings(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_kanban_columns_tenant_id ON crm_kanban_columns(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_tags_tenant_id ON crm_tags(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_leads_tenant_id ON crm_leads(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_leads_status ON crm_leads(status)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_conversations_tenant_id ON crm_conversations(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_conversations_lead_id ON crm_conversations(lead_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_conversations_status ON crm_conversations(status)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_messages_tenant_id ON crm_messages(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_messages_conversation_id ON crm_messages(conversation_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_followups_tenant_id ON crm_followups(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_followups_lead_id ON crm_followups(lead_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_followups_due_at ON crm_followups(due_at)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_followups_status ON crm_followups(status)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_tasks_tenant_id ON crm_tasks(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_tasks_lead_id ON crm_tasks(lead_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_tasks_status ON crm_tasks(status)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_activity_logs_tenant_id ON crm_activity_logs(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_activity_logs_lead_id ON crm_activity_logs(lead_id)""",
    """CREATE INDEX IF NOT EXISTS ix_crm_activity_logs_created_at ON crm_activity_logs(created_at DESC)""",
    # ===== Tools/Skills Module =====
    """CREATE TABLE IF NOT EXISTS skill_executions (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        skill_name VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        input_data TEXT,
        output_data TEXT,
        error_message TEXT,
        started_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE INDEX IF NOT EXISTS ix_skill_executions_tenant_id ON skill_executions(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_skill_executions_status ON skill_executions(status)""",
    """CREATE INDEX IF NOT EXISTS ix_skill_executions_skill_name ON skill_executions(skill_name)""",
    """CREATE INDEX IF NOT EXISTS ix_skill_executions_created_at ON skill_executions(created_at DESC)""",
    # ===== Hermes Admin Module =====
    """CREATE TABLE IF NOT EXISTS admin_tasks (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'open',
        priority VARCHAR(20) DEFAULT 'normal',
        assigned_user_id INTEGER REFERENCES users(id),
        related_tenant_id INTEGER REFERENCES tenants(id),
        due_date TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS admin_projects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'active',
        priority VARCHAR(20) DEFAULT 'normal',
        due_date TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS admin_routines (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        schedule_type VARCHAR(50) NOT NULL,
        schedule_value INTEGER NOT NULL,
        last_run_at TIMESTAMPTZ,
        next_run_at TIMESTAMPTZ,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS admin_memory (
        id SERIAL PRIMARY KEY,
        category VARCHAR(100) NOT NULL,
        key VARCHAR(255) NOT NULL,
        value TEXT NOT NULL,
        meta_data TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS admin_action_logs (
        id SERIAL PRIMARY KEY,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        entity_id INTEGER,
        details TEXT,
        performed_by_user_id INTEGER REFERENCES users(id),
        tenant_id INTEGER REFERENCES tenants(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE INDEX IF NOT EXISTS ix_admin_tasks_status ON admin_tasks(status)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_tasks_assigned_user_id ON admin_tasks(assigned_user_id)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_tasks_related_tenant_id ON admin_tasks(related_tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_projects_status ON admin_projects(status)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_routines_is_active ON admin_routines(is_active)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_routines_next_run_at ON admin_routines(next_run_at)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_memory_category ON admin_memory(category)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_memory_key ON admin_memory(key)""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_admin_memory ON admin_memory(category, key)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_action_logs_action ON admin_action_logs(action)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_action_logs_entity_type ON admin_action_logs(entity_type)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_action_logs_performed_by_user_id ON admin_action_logs(performed_by_user_id)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_action_logs_tenant_id ON admin_action_logs(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_action_logs_created_at ON admin_action_logs(created_at DESC)""",
    # ===== Admin Skills =====
    """CREATE TABLE IF NOT EXISTS admin_skills (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        trigger_type VARCHAR(50) DEFAULT 'manual',
        trigger_value VARCHAR(100),
        instructions TEXT NOT NULL,
        expected_result TEXT,
        active BOOLEAN DEFAULT TRUE,
        last_run_at TIMESTAMPTZ,
        last_run_result TEXT,
        last_run_status VARCHAR(20),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE INDEX IF NOT EXISTS ix_admin_skills_active ON admin_skills(active)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_skills_trigger_type ON admin_skills(trigger_type)""",
    """CREATE INDEX IF NOT EXISTS ix_admin_skills_last_run_at ON admin_skills(last_run_at DESC)""",
    # ===== Tenant Modules - Add missing columns =====
    """ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS kanban BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS agenda BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS instagram BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS youtube BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE tenant_modules ADD COLUMN IF NOT EXISTS content_publisher BOOLEAN NOT NULL DEFAULT FALSE""",
    # ===== Social Integrations (Instagram, YouTube) =====
    """CREATE TABLE IF NOT EXISTS social_integration_accounts (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
        provider VARCHAR(50) NOT NULL,
        provider_user_id VARCHAR(255),
        username VARCHAR(255),
        display_name VARCHAR(255),
        avatar_url TEXT,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        token_expires_at TIMESTAMPTZ,
        scope TEXT,
        status VARCHAR(50) DEFAULT 'active',
        last_error TEXT,
        webhook_url TEXT,
        last_webhook_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS social_posts (
        id SERIAL PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        integration_account_id INTEGER REFERENCES social_integration_accounts(id) ON DELETE SET NULL,
        title VARCHAR(255) NOT NULL,
        content TEXT,
        media_type VARCHAR(50) NOT NULL,
        media_url TEXT,
        thumbnail_url TEXT,
        hashtags TEXT,
        caption TEXT,
        platforms TEXT NOT NULL,
        scheduled_at TIMESTAMPTZ,
        published_at TIMESTAMPTZ,
        status VARCHAR(50) DEFAULT 'draft',
        instagram_post_id VARCHAR(255),
        instagram_media_url TEXT,
        youtube_video_id VARCHAR(255),
        youtube_video_url TEXT,
        error_message TEXT,
        error_details TEXT,
        created_by_user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    """CREATE INDEX IF NOT EXISTS ix_social_integration_accounts_tenant_id ON social_integration_accounts(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_social_integration_accounts_provider ON social_integration_accounts(provider)""",
    """CREATE INDEX IF NOT EXISTS ix_social_integration_accounts_status ON social_integration_accounts(status)""",
    """CREATE INDEX IF NOT EXISTS ix_social_posts_tenant_id ON social_posts(tenant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_social_posts_status ON social_posts(status)""",
    """CREATE INDEX IF NOT EXISTS ix_social_posts_scheduled_at ON social_posts(scheduled_at)""",
    """CREATE INDEX IF NOT EXISTS ix_social_posts_created_at ON social_posts(created_at DESC)""",
]


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        for sql in MIGRATIONS:
            try:
                conn.execute(text(sql))
            except Exception as exc:  # noqa: BLE001
                print(f"[migration] skip: {sql[:60]}... -> {exc}")


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_hermes_router)
app.include_router(integrations_router)
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(leads_router)
app.include_router(tasks_router)
app.include_router(credits_router)
app.include_router(webhook_router)
app.include_router(public_router)
app.include_router(billing_router)
app.include_router(crm_router)
app.include_router(tools_router)
