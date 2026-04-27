CREATE TABLE IF NOT EXISTS tenant_modules (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    crm BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_leads (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    origin VARCHAR(50) NOT NULL DEFAULT 'manual',
    status VARCHAR(100) NOT NULL DEFAULT 'Novo lead',
    responsible_user_id INTEGER REFERENCES users(id),
    notes TEXT,
    last_contact_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_crm_leads_tenant_phone UNIQUE (tenant_id, phone)
);

CREATE TABLE IF NOT EXISTS crm_conversations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    lead_id INTEGER REFERENCES crm_leads(id),
    chat_id INTEGER REFERENCES chats(id),
    channel VARCHAR(50) NOT NULL DEFAULT 'telegram',
    external_id VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    ai_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_user_id INTEGER REFERENCES users(id),
    last_message TEXT,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_crm_conversation_external UNIQUE (tenant_id, channel, external_id)
);

CREATE TABLE IF NOT EXISTS crm_messages (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    conversation_id INTEGER NOT NULL REFERENCES crm_conversations(id),
    legacy_message_id INTEGER REFERENCES messages(id),
    sender_type VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'telegram',
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_kanban_columns (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name VARCHAR(100) NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    color VARCHAR(20),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_crm_kanban_tenant_name UNIQUE (tenant_id, name)
);

CREATE TABLE IF NOT EXISTS crm_followups (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    lead_id INTEGER NOT NULL REFERENCES crm_leads(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pendente',
    channel VARCHAR(50) NOT NULL DEFAULT 'whatsapp',
    responsible_user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_tasks (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    responsible_user_id INTEGER REFERENCES users(id),
    due_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'pendente',
    priority VARCHAR(50) NOT NULL DEFAULT 'media',
    lead_id INTEGER REFERENCES crm_leads(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_tags (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_crm_tags_tenant_name UNIQUE (tenant_id, name)
);

CREATE TABLE IF NOT EXISTS crm_lead_tags (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    lead_id INTEGER NOT NULL REFERENCES crm_leads(id),
    tag_id INTEGER NOT NULL REFERENCES crm_tags(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_crm_lead_tag UNIQUE (tenant_id, lead_id, tag_id)
);

CREATE TABLE IF NOT EXISTS crm_activity_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    lead_id INTEGER REFERENCES crm_leads(id),
    conversation_id INTEGER REFERENCES crm_conversations(id),
    action VARCHAR(100) NOT NULL,
    description TEXT,
    metadata_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_settings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    status_options_json TEXT,
    tags_json TEXT,
    initial_auto_message TEXT,
    business_hours_json TEXT,
    hermes_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_whatsapp_connections (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    provider VARCHAR(50) NOT NULL DEFAULT 'evolution_go',
    instance_name VARCHAR(255) NOT NULL UNIQUE,
    api_base_url VARCHAR(500),
    api_key VARCHAR(500),
    webhook_url VARCHAR(500),
    status VARCHAR(50) NOT NULL DEFAULT 'disconnected',
    connected_phone VARCHAR(50),
    qr_code_base64 TEXT,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
