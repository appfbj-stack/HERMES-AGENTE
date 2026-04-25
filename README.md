# Hermes — Agente SaaS

SaaS multi-tenant de agente de atendimento com IA (DeepSeek), chat estilo WhatsApp Web, integração com Telegram (e WhatsApp preparado), controle de créditos e billing por tenant.

- **Backend:** FastAPI + PostgreSQL + SQLAlchemy + JWT
- **Frontend:** React + Vite + TypeScript + Tailwind
- **LLM:** DeepSeek (compatível OpenAI Chat)
- **Canais:** Web (interno), Telegram (pronto), WhatsApp Cloud API (preparado)
- **Deploy:** Docker / Coolify / Portainer

## URLs em produção

- API: https://api.meuchat.fbautomacao.space (`/health` para healthcheck)
- App: https://meuchat.fbautomacao.space

## Estrutura

```
agente-saas/
├─ backend/          FastAPI + SQLAlchemy + DeepSeek
├─ frontend/         React + Vite + TS + Tailwind
├─ database/         schema.sql de referência
├─ deploy/           docker-compose.yml + .env.example
├─ docs/             documentação adicional
├─ README.md
└─ .gitignore
```

## Banco de dados (PostgreSQL)

Tabelas (criadas automaticamente na primeira execução):

| Tabela            | Função                                           |
|-------------------|--------------------------------------------------|
| `tenants`         | Cliente/empresa (multi-tenant)                   |
| `users`           | Usuários do painel, vinculados a um tenant       |
| `chats`           | Conversas (web/telegram/whatsapp)                |
| `messages`        | Mensagens das conversas                          |
| `leads`           | Leads do CRM                                     |
| `tasks`           | Tarefas internas                                 |
| `credits`         | Saldo de créditos por tenant                     |
| `usage_logs`      | Auditoria de consumo da LLM                      |
| `assistant_memory`| Memória de longo prazo do agente por tenant/chat |

## Subindo localmente (Docker)

```bash
cd deploy
cp .env.example .env
# edite .env com suas chaves
docker compose up -d --build
```

- App: http://localhost:8080
- API: http://localhost:8000/health
- Postgres: localhost:5432

## Subindo em VPS via Coolify

1. **Crie um novo Project** no Coolify e adicione um **Resource → Docker Compose**.
2. Aponte para o repositório Git e a pasta `deploy/`.
3. Cole o conteúdo de `deploy/.env.example` em **Environment Variables** e ajuste:
   - `JWT_SECRET` (gere algo forte)
   - `POSTGRES_PASSWORD`
   - `DEEPSEEK_API_KEY`
   - `TELEGRAM_BOT_TOKEN` (se usar)
   - `CORS_ORIGINS=https://meuchat.fbautomacao.space`
   - `VITE_API_URL=https://api.meuchat.fbautomacao.space`
4. **Domínios:**
   - `frontend` → `https://meuchat.fbautomacao.space` (porta interna 80)
   - `backend` → `https://api.meuchat.fbautomacao.space` (porta interna 8000)
5. Habilite **Auto-deploy on push** se quiser CI/CD.
6. Deploy.

> Coolify gera certificados Let’s Encrypt automaticamente. O Cloudflare/registro do domínio precisa apontar pro IP da VPS.

## Subindo em VPS via Portainer

Cole o conteúdo de `deploy/docker-compose.yml` em **Stacks → Add stack → Web editor** e cole as variáveis de `deploy/.env.example` em **Environment variables**.

## Desenvolvimento local (sem Docker)

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# Variáveis (Windows PowerShell)
$env:DATABASE_URL="postgresql+psycopg2://agente:agente@localhost:5432/agente_saas"
$env:JWT_SECRET="dev-secret"
$env:DEEPSEEK_API_KEY="sk-..."

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Sem PostgreSQL local? Suba só o `db` do compose: `docker compose up -d db`

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 (proxy /api -> http://localhost:8000)
```

Para apontar o frontend a um backend remoto:
```bash
echo "VITE_API_URL=https://api.meuchat.fbautomacao.space" > .env.local
npm run dev
```

## Variáveis de ambiente

Veja `deploy/.env.example`. Principais:

| Variável                | Onde      | Função                                  |
|-------------------------|-----------|-----------------------------------------|
| `DATABASE_URL`          | backend   | Conexão Postgres                        |
| `JWT_SECRET`            | backend   | Segredo do JWT                          |
| `DEEPSEEK_API_KEY`      | backend   | Chave DeepSeek                          |
| `TELEGRAM_BOT_TOKEN`    | backend   | Token do bot Telegram                   |
| `TELEGRAM_WEBHOOK_SECRET`| backend  | `X-Telegram-Bot-Api-Secret-Token`       |
| `WHATSAPP_API_URL`      | backend   | Endpoint WhatsApp Cloud/Z-API           |
| `WHATSAPP_API_TOKEN`    | backend   | Bearer token da API WhatsApp            |
| `WHATSAPP_VERIFY_TOKEN` | backend   | Verificação de webhook (Meta)           |
| `CORS_ORIGINS`          | backend   | Origens liberadas (csv)                 |
| `VITE_API_URL`          | frontend  | URL pública da API                      |

## Endpoints (resumo)

```
POST   /api/auth/register
POST   /api/auth/login

GET    /api/chats
POST   /api/chats
GET    /api/chats/{id}/messages
POST   /api/chats/send

GET    /api/leads
POST   /api/leads
PATCH  /api/leads/{id}
DELETE /api/leads/{id}

GET    /api/tasks
POST   /api/tasks
PATCH  /api/tasks/{id}
DELETE /api/tasks/{id}

GET    /api/credits
GET    /api/credits/usage

POST   /api/webhooks/telegram/{tenant_id}
GET    /api/webhooks/whatsapp/{tenant_id}
POST   /api/webhooks/whatsapp/{tenant_id}

GET    /health
```

A documentação interativa fica em `https://api.meuchat.fbautomacao.space/docs`.

## Configurando o webhook do Telegram

```bash
TENANT_ID=1
BOT_TOKEN=...
SECRET=$(openssl rand -hex 32)

curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://api.meuchat.fbautomacao.space/api/webhooks/telegram/${TENANT_ID}\",
    \"secret_token\": \"${SECRET}\"
  }"
```

E configure `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` no `.env`.

## Próximos passos (não inclusos nesta versão)

- [ ] Tabela `plans` + `subscriptions` (3 planos: Starter / Pro / Enterprise)
- [ ] `tenant.subscription_status` + dependência `require_active_tenant` (bloqueio se inadimplente)
- [ ] Integração ASAAS (cobrança recorrente + créditos avulsos + webhook)
- [ ] `tenant.system_prompt` customizável (personalidade do Hermes por cliente)
- [ ] Loop de leitura/escrita em `assistant_memory` (memória de longo prazo)
- [ ] pgvector para embeddings/RAG por tenant

## Licença

Privado / proprietário.
