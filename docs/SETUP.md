# Setup detalhado

## 1. Pré-requisitos na VPS

- Docker + Docker Compose instalados
- Coolify **ou** Portainer rodando
- Domínios apontando para a VPS:
  - `meuchat.fbautomacao.space` → frontend
  - `api.meuchat.fbautomacao.space` → backend

## 2. Primeira execução

Após `docker compose up -d`:

1. Acesse `https://meuchat.fbautomacao.space/register`
2. Crie a primeira conta — isso cria o **tenant** + usuário **owner** + **10000 créditos** iniciais.
3. Copie o `tenant_id` (aparece em Configurações).

## 3. Conectar Telegram

1. Crie um bot com [@BotFather](https://t.me/BotFather) → copie o token.
2. Coloque o token em `TELEGRAM_BOT_TOKEN` no `.env`.
3. Defina `TELEGRAM_WEBHOOK_SECRET` (qualquer string secreta).
4. Configure o webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.meuchat.fbautomacao.space/api/webhooks/telegram/1",
    "secret_token": "<SECRET>"
  }'
```

5. Mande uma mensagem para o bot → ela aparece no painel de Conversas.

## 4. Conectar WhatsApp (Meta Cloud API)

1. Crie um app na [Meta for Developers](https://developers.facebook.com/) → adicione **WhatsApp Business**.
2. Pegue: `Phone Number ID`, `Access Token`, e defina um `Verify Token`.
3. No `.env`:
   ```
   WHATSAPP_API_URL=https://graph.facebook.com/v20.0/<PHONE_NUMBER_ID>/messages
   WHATSAPP_API_TOKEN=<ACCESS_TOKEN>
   WHATSAPP_VERIFY_TOKEN=<SEU_VERIFY_TOKEN>
   ```
4. No painel da Meta, configure o webhook:
   - URL: `https://api.meuchat.fbautomacao.space/api/webhooks/whatsapp/1`
   - Verify token: o mesmo do `.env`
   - Eventos: `messages`

## 5. Trocar a chave do JWT

```bash
openssl rand -hex 64
```

Cole em `JWT_SECRET` e reinicie o backend.

## 6. Backup do banco

```bash
docker exec hermes-db pg_dump -U agente agente_saas > backup_$(date +%F).sql
```

## 7. Reset de senha (manual)

Por enquanto não há fluxo automatizado. Manualmente:

```bash
docker exec -it hermes-db psql -U agente -d agente_saas
```

```sql
UPDATE users SET password_hash = '<HASH_BCRYPT>' WHERE email = 'usuario@dominio.com';
```

Para gerar o hash:
```bash
docker exec -it hermes-backend python -c "from app.core.security import hash_password; print(hash_password('nova-senha'))"
```
