# HERMES AGENTE

SaaS multi-tenant para atendimento automatizado via Telegram com IA, CRM leve e painel web estilo chat.

## Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL, JWT
- Frontend: React, Vite, TypeScript, Tailwind
- Infra: Docker, Docker Compose, Nginx
- IA: Hermes Agente como provedor principal, com DeepSeek como fallback opcional

## Estrutura

```text
backend/   API, modelos, autenticação, webhook Telegram
frontend/  painel web estilo WhatsApp
docs/      PRD, rotas e deploy
```

## Subir localmente

1. Copie `.env.example` para `.env`
2. Ajuste os segredos e tokens
3. Configure o provedor de IA no `.env`
4. Rode:

```bash
docker compose up --build
```

Frontend: `http://localhost:8080`  
Backend: `http://localhost:8000`  
Docs OpenAPI: `http://localhost:8080/api/docs`

## Bootstrap inicial

Crie o primeiro tenant e usuário admin:

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

## Integração Hermes

O projeto já sai preparado para usar o Hermes nesse endpoint:

```env
AI_PROVIDER=hermes
HERMES_AGENT_URL=https://apihermes.fbautomacao.space
HERMES_AGENT_PATH=/chat
```

Se o contrato HTTP do Hermes usar outro caminho, ajuste `HERMES_AGENT_PATH`.

Payload enviado para o Hermes:

```json
{
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ]
}
```

Resposta esperada:

```json
{
  "response": "texto"
}
```

Também aceita `content`, `answer` ou formato OpenAI compatível em `choices[0].message.content`.

## Deploy

Ver [docs/DEPLOY.md](docs/DEPLOY.md) para Coolify, Docker Compose e VPS.

## CRM Phase 1

Esta base agora inclui a fundação do módulo CRM sem recriar autenticação, cobrança,
Hermes ou a integração existente de Telegram.

### Estrutura adicionada

- tabelas `crm_*` e `tenant_modules`
- rotas `/crm/*`
- sincronização inicial de conversas e mensagens do Telegram para o CRM
- item `CRM` no menu do painel quando `tenant_modules.crm = true`

### Ativar CRM para um tenant

1. Rode a migration SQL:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_crm_phase1.sql
```

2. Ative o módulo para o tenant:

```sql
update tenant_modules
set crm = true
where tenant_id = <TENANT_ID>;
```

3. Faça login novamente no painel. O menu `CRM` passa a aparecer no frontend.

### Rotas CRM criadas

- `GET/PUT /crm/whatsapp`
- `POST /crm/whatsapp/connect`
- `GET /crm/whatsapp/status`
- `GET /crm/whatsapp/qrcode`
- `POST /crm/whatsapp/disconnect`
- `GET /crm/dashboard`
- `GET/POST /crm/leads`
- `GET/PUT/DELETE /crm/leads/{id}`
- `GET /crm/leads/{id}/activity`
- `GET /crm/conversations`
- `GET /crm/conversations/{id}`
- `PUT /crm/conversations/{id}/state`
- `POST /crm/conversations/{id}/messages`
- `GET /crm/messages?conversation_id={id}`
- `GET /crm/kanban`
- `POST /crm/kanban/move`
- `GET/POST /crm/followups`
- `GET/POST /crm/tasks`
- `GET/POST /crm/tags`
- `GET/PUT /crm/settings`
- `PUT /crm/module`

### Rotas Admin Master

- `GET /admin/tenants`
- `PUT /admin/tenants/{tenant_id}/modules`

Todas exigem login, isolamento por `tenant_id` e módulo CRM ativo.

### Escopo atual do CRM

- camada de provider WhatsApp preparada para `evolution_go`
- dashboard operacional
- CRUD visual completo de leads
- timeline básica por lead
- kanban com arrasta-e-solta
- lista de conversas do CRM
- assumir atendimento, devolver para IA e resolver conversa
- envio manual de mensagem pela tela CRM
- criação rápida de lead, follow-up e tarefa
- edição e exclusão de follow-up e tarefa pelo painel CRM
- configuração inicial de status, tags e mensagem automática
- painel master para ativar/desativar CRM por tenant
- tela CRM para conectar WhatsApp via Evolution Go

### Papel master

O painel `Master` e as rotas `/admin/*` exigem `user.role = "master"`.
Hoje isso pode ser promovido manualmente no banco para o usuário operador central.

### Evolution Go

Variáveis adicionadas para o provider:

- `EVOLUTION_API_BASE_URL`
- `EVOLUTION_API_KEY`
- `EVOLUTION_API_KEY_HEADER`

Esta integração foi estruturada como provider externo por tenant. O backend do SaaS
salva a conexão e chama a API do Evolution Go para criar instância, consultar status,
buscar QR code e desconectar.

### Webhooks de entrada

- `POST /webhook/telegram?tenant_id={tenant_id}`
- `POST /webhook/evolution-go`

Para o `evolution-go`, o backend tenta identificar a conexão por `instance_name`
no payload ou por query string. Como fallback operacional, você também pode
configurar o webhook com `?tenant_id=<TENANT_ID>&instance_name=<INSTANCE_NAME>`.

## API no frontend

Por padrão, o frontend fala com a API pelo mesmo host usando o caminho `/api`.
No container `frontend`, o `nginx` faz proxy de `/api/*` para `backend:8000`.

Se você publicar frontend e backend em domínios separados, defina `VITE_API_BASE_URL`
com a URL pública completa da API no build do frontend.

## Domínios planejados

- painel web: `https://meuchat.fbautomacao.space`
- agente Hermes: `https://apihermes.fbautomacao.space`
