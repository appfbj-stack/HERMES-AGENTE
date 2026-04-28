-- Migration: Hermes Admin Module
-- Description: Tabelas para o módulo Hermes Admin Master

-- Tabela de tarefas administrativas
CREATE TABLE IF NOT EXISTS admin_tasks (
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
);

-- Tabela de projetos administrativos
CREATE TABLE IF NOT EXISTS admin_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    priority VARCHAR(20) DEFAULT 'normal',
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de rotinas administrativas
CREATE TABLE IF NOT EXISTS admin_routines (
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
);

-- Tabela de memória da empresa
CREATE TABLE IF NOT EXISTS admin_memory (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    meta_data TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de logs de ações administrativas
CREATE TABLE IF NOT EXISTS admin_action_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details TEXT,
    performed_by_user_id INTEGER REFERENCES users(id),
    tenant_id INTEGER REFERENCES tenants(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS ix_admin_tasks_status ON admin_tasks(status);
CREATE INDEX IF NOT EXISTS ix_admin_tasks_assigned_user_id ON admin_tasks(assigned_user_id);
CREATE INDEX IF NOT EXISTS ix_admin_tasks_related_tenant_id ON admin_tasks(related_tenant_id);

CREATE INDEX IF NOT EXISTS ix_admin_projects_status ON admin_projects(status);

CREATE INDEX IF NOT EXISTS ix_admin_routines_is_active ON admin_routines(is_active);
CREATE INDEX IF NOT EXISTS ix_admin_routines_next_run_at ON admin_routines(next_run_at);

CREATE INDEX IF NOT EXISTS ix_admin_memory_category ON admin_memory(category);
CREATE INDEX IF NOT EXISTS ix_admin_memory_key ON admin_memory(key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_admin_memory ON admin_memory(category, key);

CREATE INDEX IF NOT EXISTS ix_admin_action_logs_action ON admin_action_logs(action);
CREATE INDEX IF NOT EXISTS ix_admin_action_logs_entity_type ON admin_action_logs(entity_type);
CREATE INDEX IF NOT EXISTS ix_admin_action_logs_performed_by_user_id ON admin_action_logs(performed_by_user_id);
CREATE INDEX IF NOT EXISTS ix_admin_action_logs_tenant_id ON admin_action_logs(tenant_id);
CREATE INDEX IF NOT EXISTS ix_admin_action_logs_created_at ON admin_action_logs(created_at DESC);

-- Comentários
COMMENT ON TABLE admin_tasks IS 'Tarefas administrativas internas do Hermes Admin';
COMMENT ON COLUMN admin_tasks.assigned_user_id IS 'Usuário responsável pela tarefa';
COMMENT ON COLUMN admin_tasks.related_tenant_id IS 'Tenant relacionado (se aplicável)';

COMMENT ON TABLE admin_projects IS 'Projetos administrativos do Hermes Admin';

COMMENT ON TABLE admin_routines IS 'Rotinas administrativas agendadas';
COMMENT ON COLUMN admin_routines.schedule_type IS 'Tipo de agendamento: seconds, minutes, hours, days';
COMMENT ON COLUMN admin_routines.schedule_value IS 'Valor do intervalo de agendamento';
COMMENT ON COLUMN admin_routines.is_active IS 'Se a rotina está ativa';

COMMENT ON TABLE admin_memory IS 'Memória da empresa para o Hermes Admin';
COMMENT ON COLUMN admin_memory.category IS 'Categoria da memória (ex: clientes, pagamentos, etc)';
COMMENT ON COLUMN admin_memory.key IS 'Chave única para identificar a memória';

COMMENT ON TABLE admin_action_logs IS 'Logs de ações administrativas executadas';
COMMENT ON COLUMN admin_action_logs.action IS 'Tipo de ação executada (create, update, delete, etc)';
COMMENT ON COLUMN admin_action_logs.entity_type IS 'Tipo de entidade afetada (admin_task, admin_project, etc)';
COMMENT ON COLUMN admin_action_logs.entity_id IS 'ID da entidade afetada';
COMMENT ON COLUMN admin_action_logs.performed_by_user_id IS 'Usuário que executou a ação';
COMMENT ON COLUMN admin_action_logs.tenant_id IS 'Tenant relacionado (se aplicável)';
