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
