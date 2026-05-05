# HERMES AGENTE

SaaS multi-tenant com FastAPI, PostgreSQL, painel React/Vite, CRM, Hermes Agente, Telegram, WhatsApp Evolution e deploy via Coolify.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, JWT
- Frontend: React, Vite, TypeScript, Tailwind
- Infra: Docker, Nginx, Coolify
- IA: Hermes Admin + roteamento LLM para cliente/admin

## Estrutura

```text
backend/   API, modelos, rotas, serviços, migrations e testes
frontend/  painel web admin + cliente
docs/      documentação complementar
```

## Módulos por tenant

O sistema usa `tenant_modules` com uma linha por tenant e flags por módulo:

- `crm`
- `whatsapp`
- `whatsapp_evolution`
- `kanban`
- `agenda`
- `followup`
- `instagram`
- `youtube`
- `content_publisher`

Compatibilidade legada:

- `whatsapp_evolution` mantém fallback para `whatsapp`
- `followup` mantém fallback para `crm`

API principal:

- `GET /tenant/modules`
- `GET /auth/modules`
- `PUT /admin/tenants/{tenant_id}/modules`

No backend, o helper global está em [backend/app/services/modules.py](backend/app/services/modules.py):

```python
has_module(db, tenant_id, module_key)
```

## Execução local

1. Copie `.env.example` para `.env`
2. Ajuste `DATABASE_URL`, `JWT_SECRET`/`SECRET_KEY`, credenciais admin e integrações
3. Rode:

```bash
docker compose up --build
```

URLs locais:

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8080/api/docs`

## Testes e validação

Backend:

```bash
cd backend
pytest -q
```

Frontend:

```bash
cd frontend
npx tsc -b
```

Estado atual da suíte:

- regressão backend cobrindo login, módulos, webhooks, Hermes Admin, lembretes e CRM
- build TypeScript do frontend validado

## Bootstrap inicial

```bash
curl -X POST http://localhost:8000/auth/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "token": "hermes-bootstrap",
    "tenant_name": "Demo",
    "tenant_email": "demo@empresa.com",
    "user_name": "Admin",
    "user_email": "admin@empresa.com",
    "password": "123456",
    "plan": "pro",
    "credits": 500
  }'
```

## CRM

O CRM já está integrado à base principal. Não crie projeto paralelo.

Recursos já ativos na base:

- dashboard CRM
- leads
- kanban com arrasta-e-solta
- conversas
- follow-ups
- tarefas
- configuração CRM
- integração WhatsApp Evolution
- painel Master responsivo para ativar módulos

Rotas principais:

- `GET /crm/dashboard`
- `GET/POST /crm/leads`
- `GET/PUT/DELETE /crm/leads/{id}`
- `GET /crm/kanban`
- `POST /crm/kanban/move`
- `PUT /crm/kanban/{column_id}`
- `GET/POST /crm/followups`
- `GET/POST /crm/tasks`
- `GET/POST /crm/tags`
- `GET/PUT /crm/settings`
- `GET/PUT /crm/whatsapp`

## Hermes Agente

Persistência já conectada ao banco:

- `save_memory`
- `search_memory`
- `create_task`
- `list_tasks`
- `create_reminder`
- `list_reminders`
- `create_appointment`
- `list_appointments`

Arquivos principais:

- [backend/app/services/agent.py](backend/app/services/agent.py)
- [backend/app/services/hermes_actions.py](backend/app/services/hermes_actions.py)
- [backend/app/services/hermes_admin.py](backend/app/services/hermes_admin.py)

O Hermes Admin agora possui fallback local quando a IA externa falha, em vez de quebrar o chat.

## Worker e lembretes

O scheduler de lembretes roda a cada 1 minuto:

- [backend/app/services/task_reminders.py](backend/app/services/task_reminders.py)
- [backend/app/services/scheduler.py](backend/app/services/scheduler.py)

Fluxo:

- busca tarefas vencidas e lembretes pendentes
- entrega por Telegram/WhatsApp quando aplicável
- marca como enviado

## Deploy via Coolify

### Backend

- Porta: `8000`
- Comando padrão: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Variáveis mínimas:
  - `DATABASE_URL`
  - `JWT_SECRET` ou `SECRET_KEY`
  - `ADMIN_EMAIL`
  - `ADMIN_PASSWORD`

Recomendadas:

- `CORS_ORIGINS`
- `HERMES_AGENT_URL`
- `HERMES_AGENT_PATH`
- `OPENROUTER_API_KEY`
- `DEEPSEEK_API_KEY`
- `EVOLUTION_API_BASE_URL`
- `EVOLUTION_API_KEY`

### Frontend

- Build command: padrão do Dockerfile/Vite
- `VITE_API_BASE_URL=/api` quando o frontend usa o proxy do Nginx/container
- se frontend e backend estiverem em domínios separados, use a URL pública completa da API

### Banco

- confirme `DATABASE_URL` com hostname interno válido da rede da Coolify
- se o backend não sobe e aparece erro de `could not translate host name`, o problema é DNS/rede do serviço do Postgres, não da aplicação

## Observações de produção

- o startup aplica migrations idempotentes em [backend/app/main.py](backend/app/main.py)
- há migration dedicada de padronização dos módulos em [backend/migrations/005_tenant_modules_standardization.sql](backend/migrations/005_tenant_modules_standardization.sql)
- o projeto ainda usa `@app.on_event("startup")`; funciona, mas há warning deprecatado do FastAPI
- há mudanças locais antigas no repositório fora do escopo desta rodada; revise `git status` antes de publicar tudo
