# Deploy

## Coolify

### Opção 1: Docker Compose

1. Crie um novo recurso do tipo `Docker Compose`
2. Aponte para este repositório
3. Configure as variáveis do `.env`
4. Exponha:
   - frontend na porta `80`
   - backend na porta `8000` se quiser acesso direto à API
5. Configure o webhook do Telegram usando o domínio público do backend

Por padrão, o frontend já encaminha `/api/*` para o serviço `backend:8000` via `nginx`.
Se frontend e backend ficarem no mesmo domínio, mantenha `VITE_API_BASE_URL=/api`.
Use uma URL absoluta apenas quando o frontend for buildado para consumir uma API em outro domínio.

Exemplo:

```text
https://api.seudominio.com/webhook/telegram?tenant_id=<TENANT_ID>
```

### Webhooks Telegram deste projeto

Para o ambiente padrão deste repositório, o backend público fica em:

```text
https://api.meuchat.fbautomacao.space
```

Use estas URLs:

```text
Bot Admin (super admin):
https://api.meuchat.fbautomacao.space/webhook/telegram-admin

Bot Master legado:
https://api.meuchat.fbautomacao.space/webhook/telegram-master

Bot Cliente global:
https://api.meuchat.fbautomacao.space/webhook/telegram

Bot Cliente por tenant:
https://api.meuchat.fbautomacao.space/webhook/telegram?tenant_id=<TENANT_ID>
```

Headers recomendados no Telegram:

```text
X-Telegram-Bot-Api-Secret-Token: <TOKEN_DO_BOT>
```

Mapeamento:

- `TELEGRAM_ADMIN_TOKEN`: usar com `/webhook/telegram-admin`
- `HERMES_MASTER_BOT_TOKEN`: usar com `/webhook/telegram-master`
- `TELEGRAM_CLIENT_TOKEN` ou `TELEGRAM_BOT_TOKEN`: usar com `/webhook/telegram`

Recomendação operacional:

- prefira as rotas dedicadas `/webhook/telegram-admin` e `/webhook/telegram-master` para bots administrativos
- use `/webhook/telegram` apenas para atendimento de cliente
- configure também os segredos de webhook:
  - `TELEGRAM_ADMIN_WEBHOOK_SECRET`
  - `HERMES_MASTER_WEBHOOK_SECRET`
- para bots de cliente por tenant, prefira identificar o tenant pelo token do bot do próprio tenant; use `tenant_id` na query apenas como fallback controlado

### Webhook Evolution Go

URL padrão:

```text
https://api.meuchat.fbautomacao.space/webhook/evolution-go
```

Recomendação:

- configurar a instância com `instance_name` único por tenant
- salvar `webhook_url` na conexão WhatsApp do tenant
- se necessário, usar fallback com:

```text
https://api.meuchat.fbautomacao.space/webhook/evolution-go?tenant_id=<TENANT_ID>&instance_name=<INSTANCE_NAME>
```

### Opção 2: Serviços separados

- `backend`: Dockerfile em `backend/Dockerfile`
- `frontend`: Dockerfile em `frontend/Dockerfile`
- `db`: PostgreSQL gerenciado pelo Coolify
- `redis`: opcional

## Variáveis obrigatórias

- `DATABASE_URL`
- `JWT_SECRET`
- `BOOTSTRAP_TOKEN`

## Variáveis obrigatórias por provedor de IA

- Se `AI_PROVIDER=hermes`:
  - `HERMES_AGENT_URL`
  - `HERMES_AGENT_PATH`
- Se `AI_PROVIDER=deepseek`:
  - `DEEPSEEK_API_KEY`
  - `DEEPSEEK_BASE_URL`
  - `DEEPSEEK_MODEL`

## Variáveis recomendadas para produção

- `VITE_API_BASE_URL=/api`
- `PUBLIC_PANEL_URL=https://meuchat.fbautomacao.space`
- `CORS_ORIGINS=["https://meuchat.fbautomacao.space","https://api.meuchat.fbautomacao.space"]`
- `TELEGRAM_ADMIN_TOKEN`
- `TELEGRAM_ADMIN_WEBHOOK_SECRET`
- `HERMES_MASTER_WEBHOOK_SECRET`
- `TELEGRAM_CLIENT_TOKEN` ou `TELEGRAM_BOT_TOKEN`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Domínios

- `https://meuchat.fbautomacao.space` para frontend
- `https://api.seudominio.com` ou outro domínio seu para o backend SaaS
- `https://apihermes.fbautomacao.space` para o agente Hermes externo

## Healthcheck

- endpoint: `/health`
- retorno esperado: `status=ok` e `database=ok`

## Pós-deploy

1. rode o bootstrap inicial
2. faça login no painel
3. confirme que o usuário central tenha `is_super_admin = true`
4. crie os webhooks:
   - cliente em `/webhook/telegram`
   - admin em `/webhook/telegram-admin`
   - master legado em `/webhook/telegram-master`
   - WhatsApp em `/webhook/evolution-go`
5. valide `GET /health`
6. valide envio e consumo de créditos
7. rode `cd backend && pytest` e `cd frontend && npx tsc -b` antes de promover
