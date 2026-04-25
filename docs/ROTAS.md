# Rotas

## Auth

- `POST /auth/bootstrap`
- `POST /auth/login`
- `GET /auth/me`

## Chats

- `GET /chats`
- `GET /chats/{chat_id}`
- `POST /chats/{chat_id}/assign`
- `POST /chats/{chat_id}/toggle-ai`

## Messages

- `GET /messages/{chat_id}`
- `POST /messages/{chat_id}`

## Leads

- `GET /leads`
- `POST /leads`

## Tasks

- `GET /tasks`
- `POST /tasks`

## Credits

- `GET /credits`

## Webhook

- `POST /webhook/telegram?tenant_id={tenant_id}`

Observação: para o MVP, o tenant é identificado via `tenant_id` na URL do webhook configurado no Telegram.

## Health

- `GET /health`

