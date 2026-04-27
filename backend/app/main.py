from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routes.admin import router as admin_router
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
from app.routes.webhook import router as webhook_router

settings = get_settings()

app = FastAPI(title="Hermes Agente API", version="0.2.0")
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
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(leads_router)
app.include_router(tasks_router)
app.include_router(credits_router)
app.include_router(webhook_router)
app.include_router(public_router)
app.include_router(billing_router)
app.include_router(crm_router)
