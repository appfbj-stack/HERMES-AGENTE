# Hermes Admin Master - README da Adaptação

## Visão Geral

O Hermes Admin Master é um módulo administrativo interno adicionado ao painel Admin Master existente. Ele fornece ao dono da plataforma ferramentas para gerenciar clientes, tarefas, projetos, rotinas, pagamentos, créditos e deploys, com assistência de IA.

## O que foi implementado

### Backend (6 arquivos novos/alterados)

**1. Novos Modelos (`backend/app/models.py`)**
- `AdminTask` - Tarefas administrativas internas
- `AdminProject` - Projetos administrativos
- `AdminRoutine` - Rotinas agendadas
- `AdminMemory` - Memória da empresa
- `AdminActionLog` - Logs de ações administrativas

**2. Novos Schemas (`backend/app/schemas.py`)**
- `HermesAdminChatRequest/Response` - Chat com Hermes Admin
- `AdminTaskCreate/Update/Out/ListOut` - CRUD de tarefas
- `AdminProjectCreate/Update/Out/ListOut` - CRUD de projetos
- `AdminRoutineCreate/Update/Out/ListOut` - CRUD de rotinas
- `AdminMemoryCreate/Update/Out/ListOut` - CRUD de memória
- `AdminActionLogOut/ListOut` - Logs de ações
- `HermesAdminDashboardOut` - Dashboard administrativo

**3. Novo Serviço (`backend/app/services/hermes_admin.py`)**
- `HermesAdminService` - Serviço principal com:
  - Chat com Hermes Agente (IA)
  - Dashboard com métricas da plataforma
  - CRUD de tarefas administrativas
  - CRUD de projetos administrativos
  - CRUD de rotinas agendadas
  - CRUD de memória da empresa
  - Listagem de logs de ações
  - Logging automático de ações

**4. Novas Rotas (`backend/app/routes/admin_hermes.py`)**
- `POST /admin/hermes/chat` - Chat com Hermes Admin
- `GET /admin/hermes/dashboard` - Dashboard administrativo
- `GET/POST/PATCH/DELETE /admin/hermes/tasks` - CRUD de tarefas
- `GET/POST/PATCH/DELETE /admin/hermes/projects` - CRUD de projetos
- `GET/POST/PATCH/DELETE /admin/hermes/routines` - CRUD de rotinas
- `GET/POST/PATCH/DELETE /admin/hermes/memory` - CRUD de memória
- `GET /admin/hermes/logs` - Listar logs de ações

**5. Configuração (`backend/app/core/config.py`)**
- Nova variável: `ADMIN_TELEGRAM_ID` - ID do Telegram do administrador

**6. Main (`backend/app/main.py`)**
- Router `/admin/hermes` registrado

### Frontend (3 arquivos alterados)

**1. Tipos (`frontend/src/types.ts`)**
- `HermesAdminChatResponse` - Resposta do chat
- `AdminTask` - Tipo de tarefa administrativa
- `AdminProject` - Tipo de projeto administrativo
- `AdminRoutine` - Tipo de rotina administrativa
- `AdminMemory` - Tipo de memória administrativa
- `AdminActionLog` - Tipo de log de ação
- `HermesAdminDashboard` - Tipo do dashboard

**2. API (`frontend/src/api.ts`)**
- `hermesAdminChat()` - Enviar mensagem ao Hermes
- `getHermesAdminDashboard()` - Obter dashboard
- `getAdminTasks/createAdminTask/updateAdminTask/deleteAdminTask()` - CRUD de tarefas
- `getAdminProjects/createAdminProject/updateAdminProject/deleteAdminProject()` - CRUD de projetos
- `getAdminRoutines/createAdminRoutine/updateAdminRoutine/deleteAdminRoutine()` - CRUD de rotinas
- `getAdminMemory/createAdminMemory/updateAdminMemory/deleteAdminMemory()` - CRUD de memória
- `getAdminActionLogs()` - Listar logs

**3. MasterPanel (`frontend/src/MasterPanel.tsx`)**
- Novos estados para Hermes Admin
- Botão "🤖 Hermes Admin" no painel
- Card "⚡ Atalhos Rápidos" com atalhos principais
- Componente `HermesAdminPanel` com:
  - Chat interno com Hermes Admin
  - Aba "💬 Chat" - Conversa com IA
  - Aba "✅ Tarefas" - Gerenciar tarefas internas
  - Aba "📁 Projetos" - Gerenciar projetos
  - Aba "⏰ Rotinas" - Gerenciar rotinas agendadas
  - Aba "🧠 Memória" - Memória da empresa
  - Aba "📋 Logs" - Log de ações administrativas

### Database (1 migration)

**Migration 003 (`backend/migrations/003_hermes_admin.sql`)**
- Tabela `admin_tasks` - Tarefas administrativas
- Tabela `admin_projects` - Projetos administrativos
- Tabela `admin_routines` - Rotinas agendadas
- Tabela `admin_memory` - Memória da empresa
- Tabela `admin_action_logs` - Logs de ações
- Índices em todas as tabelas para performance

### Configuração (.env)

**Nova variável:**
```env
ADMIN_TELEGRAM_ID=123456789
```

## Como usar

### 1. Aplicar migration

```bash
# Via Docker Compose
docker compose exec db psql -U postgres -d hermes -f /app/migrations/003_hermes_admin.sql

# Ou direto no PostgreSQL
psql "$DATABASE_URL" -f backend/migrations/003_hermes_admin.sql
```

### 2. Configurar variável de ambiente

No `.env` ou no Coolify:
```env
ADMIN_TELEGRAM_ID=seu_telegram_id
```

### 3. Fazer deploy

```bash
docker compose down
docker compose up --build
```

### 4. Acessar Hermes Admin

1. Faça login como super admin
2. Acesse o painel Master
3. Clique no botão "🤖 Hermes Admin"
4. Use o chat para interagir com o assistente

## Funcionalidades

### Chat com Hermes Admin

O Hermes Admin é um assistente de IA que pode:
- Responder perguntas sobre a plataforma
- Listar clientes ativos/bloqueados
- Ver pagamentos pendentes
- Sugerir criação de tarefas e rotinas
- Consultar memória da empresa
- Fornecer resumo diário

**Exemplos de comandos:**
- "Quais clientes estão ativos?"
- "Liste os clientes bloqueados"
- "Crie uma tarefa para verificar pagamentos"
- "Qual o resumo de hoje?"
- "Quanto usei de mensagens este mês?"

### Tarefas Administrativas

Gerencie tarefas internas da equipe:
- Criar tarefas relacionadas a clientes
- Atribuir responsáveis
- Definir prioridades (baixa, normal, alta, urgente)
- Definir datas de vencimento
- Marcar como concluídas

### Projetos Administrativos

Gerencie projetos da plataforma:
- Criar novos projetos
- Definir descrições e prioridades
- Definir prazos
- Acompanhar progresso

### Rotinas Agendadas

Configure rotinas automáticas:
- Agendar tarefas recorrentes
- Definir intervalo (segundos, minutos, horas, dias)
- Ativar/desativar rotinas
- Ver histórico de execuções

### Memória da Empresa

Armazene conhecimento corporativo:
- Salvar informações importantes sobre clientes
- Documentar processos
- Categorizar informações
- Buscar rapidamente

### Logs de Ações

Auditoria completa de:
- Criações e atualizações
- Usuário que executou a ação
- Timestamp da ação
- Detalhes da operação

## Segurança

- Todas as rotas exigem `is_super_admin = true`
- Usuários comuns não têm acesso
- Clientes tenants não têm acesso
- Logs de todas as ações são registrados
- Dados isolados corretamente

## Prompt do Hermes Admin

```
Você é o Hermes Admin Master, assistente interno da plataforma HERMES AGENTE.

Seu objetivo: Ajudar o dono da plataforma a organizar clientes, projetos, tarefas, rotinas, pagamentos, créditos e deploys.

REGRAS IMPORTANTES:
- Você pode consultar dados globais da plataforma (tenants, créditos, pagamentos)
- NUNCA misture dados de clientes diferentes
- Antes de ações críticas (deletar, bloquear), peça confirmação
- Ao identificar tarefas, rotinas ou informações importantes, sugira salvar no banco
- Sempre que criar uma tarefa ou rotina, peça confirmação antes de salvar
- Responda de forma direta, prática e em português
```



## Skills / Rotinas Internas

O Hermes Admin pode criar, salvar e executar skills/rotinas internas automaticamente.

### Criar Skill via Chat

O Hermes Admin pode analisar conversas e sugerir criação de skills:

`
Usuário: Hermes, toda segunda gere um resumo dos clientes com pagamento vencido.
Sistema: Analisa e sugere skill
Usuário: Confirma criação
Sistema: Cria skill e salva no banco
`

### Tipos de Trigger

- manual - Execução apenas manual
- daily - Diário em horário específico (ex: 09:00)
- weekly - Semanal em dia específico (ex: monday_08:00)
- monthly - Mensal no dia X (ex: 01_09:00)

### Executar Skill

`ash
# Executar manualmente
curl -X POST /admin/hermes/skills/{id}/run
`

### Skills Pré-Implementadas

- 
esumo_pagamentos_vencidos - Resumo de clientes vencidos
- listar_clientes_ativos - Lista clientes ativos
- listar_clientes_bloqueados - Lista clientes bloqueados
- dashboard_completo - Dashboard completo

**Documentação completa:** [Admin Skills](./ADMIN_SKILLS.md)


## Integração Telegram Admin (Plano futuro)

Para implementar comandos do Telegram:
1. Configurar `ADMIN_TELEGRAM_ID` no `.env`
2. Adaptar webhook existente para reconhecer comandos admin
3. Implementar comandos como `/admin_summary`, `/admin_tasks`, etc.
4. Apenas o ID configurado pode executar comandos

## Checklist de Teste

### Backend

- [ ] Migration aplicada com sucesso
- [ ] Rotas `/admin/hermes/*` estão acessíveis
- [ ] Chat com Hermes responde corretamente
- [ ] Dashboard retorna métricas corretas
- [ ] CRUD de tarefas funciona
- [ ] CRUD de projetos funciona
- [ ] CRUD de rotinas funciona
- [ ] CRUD de memória funciona
- [ ] Logs são registrados
- [ ] Usuário comum não acessa rotas admin

### Frontend

- [ ] Botão "🤖 Hermes Admin" aparece no painel
- [ ] Card "⚡ Atalhos Rápidos" aparece
- [ ] Modal Hermes Admin abre corretamente
- [ ] Chat envia e recebe mensagens
- [ ] Abas funcionam corretamente
- [ ] Atalhos funcionam
- [ ] Mensagens de erro são exibidas

### Integração

- [ ] Hermes Agente está configurado
- [ ] Token do Hermes está correto
- [ ] Dashboard mostra dados reais
- [ ] Chat responde em português
- [ ] Ações sugeridas funcionam

## Troubleshooting

### Hermes não responde
- Verifique `HERMES_AGENT_URL` e `HERMES_AGENT_PATH`
- Verifique `HERMES_AGENT_API_KEY`
- Verifique se o Hermes está online

### Usuário comum acessa rotas admin
- Verifique se `is_super_admin` está `true` no banco
- Limpe o cache e faça login novamente

### Dashboard mostra zeros
- Verifique se há tenants cadastrados
- Verifique se migration foi aplicada
- Recarregue a página

### Erro 403 Forbidden
- Verifique se usuário é super admin
- Verifique token JWT
- Limpe localStorage

## Próximas Melhorias

1. Implementar CRUD completo de tarefas no frontend
2. Implementar CRUD completo de projetos no frontend
3. Implementar CRUD completo de rotinas no frontend
4. Implementar CRUD completo de memória no frontend
5. Implementar listagem de logs no frontend
6. Implementar integração Telegram Admin
7. Adicionar filtros e busca em listagens
8. Adicionar exportação de dados
9. Adicionar gráficos no dashboard
10. Adicionar notificações de rotinas

## Suporte

Para dúvidas ou problemas:
1. Verifique este README
2. Consulte a documentação do Hermes Agente
3. Verifique os logs do backend
4. Verifique o console do navegador
