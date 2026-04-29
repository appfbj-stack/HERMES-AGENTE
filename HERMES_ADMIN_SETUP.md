# Guia de Configuração do Hermes Admin

## Passo 1: Configurar Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```bash
# API Keys para LLMs (OBRIGATÓRIO)
OPENROUTER_API_KEY=sk-or-v1-sua_chave_aqui
DEEPSEEK_API_KEY=sk-sua_chave_aqui

# Telegram Bots (OBRIGATÓRIO)
TELEGRAM_BOT_TOKEN=seu_bot_token_cliente
TELEGRAM_ADMIN_TOKEN=seu_bot_token_admin
HERMES_MASTER_BOT_TOKEN=seu_bot_token_master
HERMES_MASTER_BOT_USERNAME=seu_bot_username

# Outras configurações
DATABASE_URL=postgresql+psycopg://postgres:senha@db:5432/hermes
JWT_SECRET=seu_jwt_secret_aqui
```

## Passo 2: Criar Bots no Telegram

### Bot para Clientes

1. Converse com @BotFather no Telegram
2. Use `/newbot`
3. Siga as instruções
4. Copie o token gerado
5. Adicione como `TELEGRAM_BOT_TOKEN` no `.env`

### Bot Admin (Hermes Admin Master)

1. Converse com @BotFather no Telegram
2. Use `/newbot`
3. Nome: "Hermes Admin Master" (ou preferido)
4. Username: deve ser único
5. Copie o token gerado
6. Adicione como `TELEGRAM_ADMIN_TOKEN` no `.env`

### Bot Master (existente)

Se já tiver um bot master:
1. Use o token existente
2. Adicione como `HERMES_MASTER_BOT_TOKEN` no `.env`
3. Adicione o username como `HERMES_MASTER_BOT_USERNAME`

## Passo 3: Configurar Webhooks

### Webhook para Bot Admin

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_ADMIN_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-dominio.com/api/webhook/telegram-admin",
    "secret_token": "your_secret_token_here"
  }'
```

### Webhook para Bot Master (se necessário)

```bash
curl -X POST "https://api.telegram.org/bot<HERMES_MASTER_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-dominio.com/api/webhook/telegram-master",
    "secret_token": "your_secret_token_here"
  }'
```

### Webhook para Bot Cliente (existente)

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-dominio.com/api/webhook/telegram",
    "secret_token": "your_secret_token_here"
  }'
```

## Passo 4: Criar Super Admin

### Via Painel Web

1. Acesse `https://seu-dominio.com/login`
2. Faça login com a primeira conta criada
3. O primeiro usuário é automaticamente promovido a `is_super_admin=True`
4. Acesse `/admin/hermes` para usar o Hermes Admin

### Via Banco de Dados (opcional)

```sql
UPDATE users SET is_super_admin = TRUE WHERE email = 'seu_email@exemplo.com';
```

## Passo 5: Testar Integração

### Testar via API

```bash
# Login para obter token
curl -X POST "https://seu-dominio.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu_email@exemplo.com",
    "password": "sua_senha"
  }'

# Testar Hermes Admin
curl -X POST "https://seu-dominio.com/api/admin/hermes/chat" \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"message": "status do sistema"}'
```

### Testar via Telegram

1. Inicie uma conversa com o bot admin
2. Envie: "status do sistema"
3. Verifique se recebe resposta

### Testar via Script

```bash
python test_hermes_integration.py
```

## Passo 6: Configurar Skills Administrativas

### Criar Skill via Painel

1. Acesse `/admin/hermes`
2. Vá para "Skills"
3. Clique em "Nova Skill"
4. Preencha:
   - Nome: "Dashboard Diário"
   - Descrição: "Gera resumo diário do sistema"
   - Trigger Type: "manual"
   - Instruções: "Gerar dashboard completo com todos os tenants e métricas"
5. Salve

### Criar Skill via API

```bash
curl -X POST "https://seu-dominio.com/api/admin/hermes/skills" \
  -H "Authorization: Bearer SEU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dashboard_diario",
    "description": "Gera resumo diário do sistema",
    "trigger_type": "manual",
    "instructions": "Gerar dashboard completo com todos os tenants e métricas",
    "active": true
  }'
```

## Passo 7: Monitoramento

### Ver Logs

```bash
# Ver logs do aplicativo
tail -f logs/app.log

# Filtrar por Hermes Admin
grep "Hermes Admin" logs/app.log

# Filtrar por LLM Router
grep "LLM Router" logs/app.log
```

### Ver Dashboard

1. Acesse `/admin/hermes/dashboard`
2. Visualize métricas em tempo real
3. Monitore:
   - Clientes ativos
   - Créditos usados
   - Tarefas abertas
   - Rotinas ativas

## Troubleshooting

### Problema: Hermes Admin não responde

**Solução:**
1. Verifique se `OPENROUTER_API_KEY` está configurada
2. Verifique logs: `logs/app.log`
3. Teste API key:
   ```bash
   curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "z-ai/glm-4.7", "messages": [{"role": "user", "content": "test"}]}'
   ```

### Problema: Telegram Admin não recebe mensagens

**Solução:**
1. Verifique se webhook está configurado:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```
2. Verifique se URL está acessível
3. Verifique logs do servidor

### Problema: Erro de autenticação

**Solução:**
1. Verifique se usuário tem `is_super_admin=True`
2. Verifique se token JWT é válido
3. Faça login novamente para obter novo token

### Problema: Banco de dados não conecta

**Solução:**
1. Verifique se PostgreSQL está rodando
2. Verifique se `DATABASE_URL` está correta
3. Verifique se usuário e senha estão corretos
4. Teste conexão:
   ```bash
   psql $DATABASE_URL
   ```

## Manutenção

### Backup Diário

Adicione ao crontab:

```bash
0 2 * * * /path/to/backup_script.sh
```

### Limpeza de Logs

Configurar rotação automática no `app/core/logging.py`

### Atualizações

1. Pull do repositório
2. Rodar migrações
3. Reiniciar serviço
4. Testar integração

## Suporte

Em caso de problemas:

1. Verificar logs: `logs/app.log`
2. Rodar testes: `python test_hermes_integration.py`
3. Consultar documentação: `HERMES_ADMIN_INTEGRATION.md`
4. Abrir issue no GitHub

## Segurança

### Boas Práticas

1. Nunca comitar `.env` no git
2. Usar valores fortes para secrets
3. Rotacionar chaves periodicamente
4. Monitorar logs de acesso
5. Usar HTTPS em produção

### Permissões

- Super Admin: Acesso total
- Usuário Comum: Acesso apenas ao tenant
- NUNCA misturar dados entre tenants

## Performance

### Otimizações

1. Usar cache para queries frequentes
2. Limitar tamanho de contexto
3. Usar índices no banco
4. Monitorar tempo de resposta

### Monitoramento

1. Logs de uso de LLM
2. Métricas de performance
3. Alertas de erro
4. Análise de custos

## Próximos Passos

1. Configurar notificações push
2. Implementar dashboard em tempo real
3. Adicionar mais skills administrativas
4. Integrar com Coolify para deploy
5. Criar app mobile para admin