-- Schema de referência (PostgreSQL).
-- O backend cria as tabelas automaticamente via SQLAlchemy (Base.metadata.create_all).
-- Este arquivo serve como documentação ou para inicializar manualmente.

CREATE TABLE IF NOT EXISTS tenants (
  id           SERIAL PRIMARY KEY,
  name         VARCHAR(255) NOT NULL,
  slug         VARCHAR(64) UNIQUE NOT NULL,
  plan         VARCHAR(32) DEFAULT 'free',
  created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

CREATE TABLE IF NOT EXISTS users (
  id            SERIAL PRIMARY KEY,
  tenant_id     INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name          VARCHAR(255) NOT NULL,
  role          VARCHAR(32) DEFAULT 'member',
  is_active     BOOLEAN DEFAULT TRUE,
  created_at    TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS chats (
  id              SERIAL PRIMARY KEY,
  tenant_id       INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  channel         VARCHAR(32) DEFAULT 'web',
  external_id     VARCHAR(255),
  contact_name    VARCHAR(255),
  contact_phone   VARCHAR(64),
  last_message_at TIMESTAMP DEFAULT NOW(),
  created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chats_tenant ON chats(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chats_external ON chats(external_id);

CREATE TABLE IF NOT EXISTS messages (
  id          SERIAL PRIMARY KEY,
  chat_id     INT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
  role        VARCHAR(16) NOT NULL,
  content     TEXT NOT NULL,
  tokens_in   INT DEFAULT 0,
  tokens_out  INT DEFAULT 0,
  created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

CREATE TABLE IF NOT EXISTS leads (
  id          SERIAL PRIMARY KEY,
  tenant_id   INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  chat_id     INT REFERENCES chats(id) ON DELETE SET NULL,
  name        VARCHAR(255) NOT NULL,
  email       VARCHAR(255),
  phone       VARCHAR(64),
  status      VARCHAR(32) DEFAULT 'new',
  notes       TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads(tenant_id);

CREATE TABLE IF NOT EXISTS tasks (
  id          SERIAL PRIMARY KEY,
  tenant_id   INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     INT REFERENCES users(id) ON DELETE SET NULL,
  title       VARCHAR(255) NOT NULL,
  description TEXT,
  status      VARCHAR(32) DEFAULT 'pending',
  due_at      TIMESTAMP,
  created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);

CREATE TABLE IF NOT EXISTS credits (
  id          SERIAL PRIMARY KEY,
  tenant_id   INT NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
  balance     INT DEFAULT 0,
  updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_logs (
  id            SERIAL PRIMARY KEY,
  tenant_id     INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  chat_id       INT REFERENCES chats(id) ON DELETE SET NULL,
  provider      VARCHAR(32) DEFAULT 'deepseek',
  model         VARCHAR(64) DEFAULT 'deepseek-chat',
  tokens_in     INT DEFAULT 0,
  tokens_out    INT DEFAULT 0,
  cost_credits  INT DEFAULT 0,
  created_at    TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_tenant ON usage_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_logs(created_at);

CREATE TABLE IF NOT EXISTS assistant_memory (
  id          SERIAL PRIMARY KEY,
  tenant_id   INT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  chat_id     INT REFERENCES chats(id) ON DELETE CASCADE,
  key         VARCHAR(128) NOT NULL,
  value       TEXT NOT NULL,
  updated_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_memory_tenant ON assistant_memory(tenant_id);
