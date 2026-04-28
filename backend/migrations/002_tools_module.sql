-- Migration: Tools/Skills Module
-- Description: Adiciona tabela para log de execuções de skills/ferramentas

-- Tabela de execuções de skills
CREATE TABLE IF NOT EXISTS skill_executions (
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
);

-- Índices
CREATE INDEX IF NOT EXISTS ix_skill_executions_tenant_id ON skill_executions(tenant_id);
CREATE INDEX IF NOT EXISTS ix_skill_executions_status ON skill_executions(status);
CREATE INDEX IF NOT EXISTS ix_skill_executions_skill_name ON skill_executions(skill_name);
CREATE INDEX IF NOT EXISTS ix_skill_executions_created_at ON skill_executions(created_at DESC);

-- Comentários
COMMENT ON TABLE skill_executions IS 'Histórico de execuções de skills/ferramentas por tenant';
COMMENT ON COLUMN skill_executions.tenant_id IS 'ID do tenant (isolação multi-tenant)';
COMMENT ON COLUMN skill_executions.skill_name IS 'Nome da skill executada (github, coolify, file_reader, etc)';
COMMENT ON COLUMN skill_executions.status IS 'Status da execução: pending, running, completed, failed';
COMMENT ON COLUMN skill_executions.input_data IS 'Dados de entrada da execução (JSON ou texto)';
COMMENT ON COLUMN skill_executions.output_data IS 'Dados de saída da execução (JSON ou texto)';
COMMENT ON COLUMN skill_executions.error_message IS 'Mensagem de erro em caso de falha';
COMMENT ON COLUMN skill_executions.started_at IS 'Timestamp de início da execução';
COMMENT ON COLUMN skill_executions.completed_at IS 'Timestamp de conclusão da execução';
