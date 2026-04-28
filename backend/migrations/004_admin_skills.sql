-- Migration: Admin Skills
-- Description: Tabela para skills/rotinas administrativas do Hermes Admin

-- Tabela de skills administrativas
CREATE TABLE IF NOT EXISTS admin_skills (
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
);

-- Índices
CREATE INDEX IF NOT EXISTS ix_admin_skills_active ON admin_skills(active);
CREATE INDEX IF NOT EXISTS ix_admin_skills_trigger_type ON admin_skills(trigger_type);
CREATE INDEX IF NOT EXISTS ix_admin_skills_last_run_at ON admin_skills(last_run_at DESC);

-- Comentários
COMMENT ON TABLE admin_skills IS 'Skills/rotinas administrativas executáveis pelo Hermes Admin';
COMMENT ON COLUMN admin_skills.name IS 'Nome único da skill';
COMMENT ON COLUMN admin_skills.description IS 'Descrição do objetivo da skill';
COMMENT ON COLUMN admin_skills.trigger_type IS 'Tipo de disparo: manual, daily, weekly, monthly, cron';
COMMENT ON COLUMN admin_skills.trigger_value IS 'Valor do disparo (ex: monday, 08:00, daily_09:00)';
COMMENT ON COLUMN admin_skills.instructions IS 'Instruções detalhadas da skill';
COMMENT ON COLUMN admin_skills.expected_result IS 'Resultado esperado da execução';
COMMENT ON COLUMN admin_skills.active IS 'Se a skill está ativa para execução';
COMMENT ON COLUMN admin_skills.last_run_at IS 'Timestamp da última execução';
COMMENT ON COLUMN admin_skills.last_run_result IS 'Resultado da última execução';
COMMENT ON COLUMN admin_skills.last_run_status IS 'Status da última execução: completed, failed, pending';
