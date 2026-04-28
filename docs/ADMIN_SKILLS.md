# Admin Skills - Módulo de Rotinas Internas

## Visão Geral

O módulo Admin Skills permite que o Hermes Admin crie, salve e execute skills/rotinas internas automaticamente ou manualmente. As skills são tarefas repetitivas que podem ser agendadas e executadas pelo sistema.

## Estrutura da Tabela

**Tabela: `admin_skills`**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | SERIAL | Identificador único |
| `name` | VARCHAR(255) | Nome único da skill |
| `description` | TEXT | Descrição do objetivo |
| `trigger_type` | VARCHAR(50) | Tipo de disparo: manual, daily, weekly, monthly, cron |
| `trigger_value` | VARCHAR(100) | Valor do disparo (ex: monday, 08:00) |
| `instructions` | TEXT | Instruções detalhadas da skill |
| `expected_result` | TEXT | Resultado esperado |
| `active` | BOOLEAN | Se está ativa para execução |
| `last_run_at` | TIMESTAMPTZ | Timestamp da última execução |
| `last_run_result` | TEXT | Resultado da última execução |
| `last_run_status` | VARCHAR(20) | Status: completed, failed, pending |
| `created_at` | TIMESTAMPTZ | Timestamp de criação |
| `updated_at` | TIMESTAMPTZ | Timestamp de atualização |

## Rotas Disponíveis

### CRUD de Skills

#### `GET /admin/hermes/skills`
Lista skills administrativas.

**Query params:**
- `active_only` (bool): Apenas skills ativas (default: false)
- `limit` (int): Limite de resultados (default: 50)
- `offset` (int): Offset (default: 0)

**Response:**
```json
{
  "skills": [...],
  "total": 10
}
```

#### `POST /admin/hermes/skills`
Cria nova skill administrativa.

**Request:**
```json
{
  "name": "resumo_pagamentos_vencidos",
  "description": "Gera resumo de clientes com pagamentos vencidos",
  "trigger_type": "weekly",
  "trigger_value": "monday_08:00",
  "instructions": "Consultar tenants vencidos, pagamentos Asaas e gerar resumo",
  "expected_result": "Relatório em formato texto com lista de clientes",
  "active": true
}
```

**Response:**
```json
{
  "id": 1,
  "name": "resumo_pagamentos_vencidos",
  "description": "...",
  "trigger_type": "weekly",
  "trigger_value": "monday_08:00",
  "instructions": "...",
  "expected_result": "...",
  "active": true,
  "last_run_at": null,
  "last_run_result": null,
  "last_run_status": null,
  "created_at": "2024-04-28T10:00:00Z",
  "updated_at": "2024-04-28T10:00:00Z"
}
```

#### `PATCH /admin/hermes/skills/{skill_id}`
Atualiza skill administrativa.

**Request:** Parcial, apenas campos que deseja atualizar.

#### `DELETE /admin/hermes/skills/{skill_id}`
Deleta skill administrativa.

### Execução de Skills

#### `POST /admin/hermes/skills/{skill_id}/run`
Executa uma skill manualmente.

**Request:**
```json
{
  "parameters": {
    "param1": "value1"
  }
}
```

**Response:**
```json
{
  "skill_id": 1,
  "skill_name": "resumo_pagamentos_vencidos",
  "status": "completed",
  "result": {
    "type": "resumo_pagamentos_vencidos",
    "summary": "📊 Resumo de Pagamentos Vencidos...",
    "blocked_clients": 3,
    "output": "..."
  },
  "error": null,
  "execution_time": 2.5,
  "executed_at": "2024-04-28T10:00:00Z"
}
```

### Sugestão de Skills

#### `POST /admin/hermes/skills/suggest`
Sugere criação de skill a partir da conversa.

**Request:**
```json
{
  "message": "Hermes, toda segunda gere um resumo dos clientes com pagamento vencido."
}
```

**Response:**
```json
{
  "success": true,
  "suggestion": {
    "name": "resumo_semanal_pagamentos_vencidos",
    "description": "Gera resumo semanal de clientes com pagamentos vencidos",
    "trigger_type": "weekly",
    "trigger_value": "monday_08:00",
    "instructions": "Consultar tenants vencidos, pagamentos Asaas e gerar resumo semanal",
    "expected_result": "Relatório em formato texto",
    "active": true
  },
  "confidence": 0.85,
  "reason": "Conversa indica necessidade de rotina semanal de resumo de pagamentos"
}
```

## Tipos de Trigger

| Tipo | Descrição | Exemplo de valor |
|------|-----------|------------------|
| `manual` | Execução apenas manual | - |
| `daily` | Diário em horário específico | `09:00`, `14:30` |
| `weekly` | Semanal em dia específico | `monday_08:00`, `friday_17:00` |
| `monthly` | Mensal no dia X | `01_09:00`, `15_14:00` |
| `cron` | Expressão cron completa | `0 9 * * 1` (segunda às 9h) |

## Skills Pré-Implementadas

O Hermes Admin já vem com algumas skills pré-implementadas:

### 1. `resumo_pagamentos_vencidos`
- **Descrição:** Gera resumo de clientes com pagamentos vencidos
- **Instruções:** `Consultar tenants vencidos, pagamentos Asaas e gerar resumo`
- **Tipo:** weekly
- **Valor:** monday_08:00

### 2. `listar_clientes_ativos`
- **Descrição:** Lista todos os clientes ativos
- **Instruções:** `Listar todos os clientes ativos da plataforma`
- **Tipo:** manual
- **Valor:** -

### 3. `listar_clientes_bloqueados`
- **Descrição:** Lista clientes bloqueados (sem créditos)
- **Instruções:** `Listar todos os clientes bloqueados por falta de créditos`
- **Tipo:** manual
- **Valor:** -

### 4. `dashboard_completo`
- **Descrição:** Gera dashboard completo da plataforma
- **Instruções:** `Gerar dashboard com todas as métricas da plataforma`
- **Tipo:** manual
- **Valor:** -

## Fluxo de Uso

### 1. Criar Skill Manualmente

```bash
# Criar nova skill
curl -X POST http://localhost:8000/api/admin/hermes/skills \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resumo_diario",
    "description": "Resumo diário de atividades",
    "trigger_type": "daily",
    "trigger_value": "09:00",
    "instructions": "Gerar resumo diário de atividades da plataforma",
    "active": true
  }'
```

### 2. Criar Skill via Chat Hermes

```
Usuário: Hermes, cria uma skill que roda toda segunda às 9h para listar clientes bloqueados
Sistema: Analisa e sugere skill
Usuário: Confirma criação
Sistema: Cria skill e salva no banco
```

### 3. Executar Skill Manualmente

```bash
# Executar skill manualmente
curl -X POST http://localhost:8000/api/admin/hermes/skills/1/run \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 4. Listar Skills

```bash
# Listar todas as skills
curl -X GET http://localhost:8000/api/admin/hermes/skills \
  -H "Authorization: Bearer YOUR_TOKEN"

# Listar apenas skills ativas
curl -X GET "http://localhost:8000/api/admin/hermes/skills?active_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Integração com Hermes Admin Chat

O Hermes Admin pode:
- **Analisar conversa** e sugerir criação de skills
- **Pedir confirmação** antes de criar skill
- **Executar skills** a pedido do usuário
- **Mostrar resultados** das execuções
- **Sugerir melhorias** em rotinas existentes

### Exemplo de Conversa

```
Usuário: Hermes, toda segunda gere um resumo dos clientes com pagamento vencido.

Hermes: 🤖 Analisando sua solicitação...

✅ Suggesto criar a seguinte skill:

Nome: resumo_semanal_pagamentos_vencidos
Descrição: Gera resumo semanal de clientes com pagamentos vencidos
Quando: Toda segunda às 08:00
Instruções: Consultar tenants vencidos, pagamentos Asaas e gerar resumo

Confirma a criação? (sim/não)

Usuário: sim

Hermes: ✅ Skill criada com sucesso!

Skill ID: 1
Próxima execução: Segunda 08:00

Deseja executar agora para teste? (sim/não)

Usuário: sim

Hermes: 🚀 Executando skill...

✅ Execução concluída!

📊 Resumo de Pagamentos Vencidos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total de clientes: 10
Clientes bloqueados: 3

• Cliente A (email@exemplo.com)
  Créditos restantes: 0 / 1000
  Usados: 1000
...
```

## Exemplos de Skills

### Exemplo 1: Relatório Diário de Vendas

```json
{
  "name": "relatorio_vendas_diario",
  "description": "Gera relatório diário de vendas e novos clientes",
  "trigger_type": "daily",
  "trigger_value": "18:00",
  "instructions": "Consultar tenants criados hoje, créditos adicionados, pagamentos recebidos e gerar relatório",
  "expected_result": "Relatório em formato texto com métricas do dia"
}
```

### Exemplo 2: Backup Automático

```json
{
  "name": "backup_diario",
  "description": "Executa backup diário do banco de dados",
  "trigger_type": "daily",
  "trigger_value": "02:00",
  "instructions": "Executar pg_dump do banco PostgreSQL e salvar em S3",
  "expected_result": "Backup salvo com sucesso",
  "active": true
}
```

### Exemplo 3: Limpeza de Logs

```json
{
  "name": "limpeza_logs_mensal",
  "description": "Remove logs antigos para economizar espaço",
  "trigger_type": "monthly",
  "trigger_value": "01_03:00",
  "instructions": "Remover logs de ações administrativas com mais de 90 dias",
  "expected_result": "Logs antigos removidos",
  "active": true
}
```

## Status de Execução

| Status | Descrição |
|--------|-----------|
| `completed` | Skill executada com sucesso |
| `failed` | Erro na execução da skill |
| `pending` | Aguardando execução |

## Segurança

- Todas as rotas exigem `is_super_admin = true`
- Skills só podem ser criadas/editadas por super admin
- Logs de todas as execuções são registrados
- Skills inativas não podem ser executadas
- Execução assíncrona para não bloquear a API

## Troubleshooting

### Skill não executa
- Verifique se a skill está `active: true`
- Verifique se as instruções estão corretas
- Verifique logs de erro em `last_run_result`

### Sugestão de skill não funciona
- Verifique se Hermes Agente está configurado
- Verifique se a mensagem é clara
- Tente reformular a solicitação

### Trigger não funciona
- Verifique `trigger_type` e `trigger_value`
- Para tipos `daily/weekly/monthly`, use formato: `HH:MM` ou `day_HH:MM`
- Para `cron`, use expressão cron válida

## Próximas Melhorias

1. [ ] Scheduler automático para executar skills agendadas
2. [ ] Interface visual para criar/editar skills no frontend
3. [ ] Histórico completo de execuções
4. [ ] Notificações de execução (Telegram, Email)
5. [ ] Encadeamento de skills (workflow)
6. [ ] Variáveis dinâmicas nas instruções
7. [ ] Templates de skills pré-definidos
8. [ ] Exportação/importação de skills
9. [ ] Teste de skills antes de salvar
10. [ ] Dashboard de execução de skills

## Migration

```bash
# Via Docker Compose
docker compose exec db psql -U postgres -d hermes -f /app/migrations/004_admin_skills.sql

# Ou direto no PostgreSQL
psql "$DATABASE_URL" -f backend/migrations/004_admin_skills.sql
```

## Documentação Relacionada

- [Hermes Admin](./HERMES_ADMIN.md) - Documentação geral do Hermes Admin
- [Tools/Skills](./TOOLS.md) - Módulo de ferramentas e skills do sistema
- [API Routes](../backend/app/routes/admin_hermes.py) - Implementação das rotas
