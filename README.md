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
Docs OpenAPI: `http://localhost:8000/docs`

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

## Domínios planejados

- painel web: `https://meuchat.fbautomacao.space`
- agente Hermes: `https://apihermes.fbautomacao.space`
