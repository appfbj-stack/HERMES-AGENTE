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

### Opção 2: Serviços separados

- `backend`: Dockerfile em `backend/Dockerfile`
- `frontend`: Dockerfile em `frontend/Dockerfile`
- `db`: PostgreSQL gerenciado pelo Coolify
- `redis`: opcional

## Variáveis obrigatórias

- `DATABASE_URL`
- `JWT_SECRET`
- `AI_PROVIDER`
- `HERMES_AGENT_URL`
- `DEEPSEEK_API_KEY`
- `BOOTSTRAP_TOKEN`

## Domínios

- `https://meuchat.fbautomacao.space` para frontend
- `https://api.seudominio.com` ou outro domínio seu para o backend SaaS
- `https://apihermes.fbautomacao.space` para o agente Hermes externo

## Healthcheck

- endpoint: `/health`

## Pós-deploy

1. rode o bootstrap inicial
2. faça login no painel
3. crie o webhook do Telegram com o `tenant_id`
4. valide envio e consumo de créditos
