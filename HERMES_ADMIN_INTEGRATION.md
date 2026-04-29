# Hermes Admin Integration

## Visão Geral

O sistema Hermes AGENTE agora possui integração completa com o Hermes Admin Master, permitindo gerenciamento administrativo via Telegram e painel web.

## Arquitetura

### LLM Router Inteligente

O sistema possui um roteador inteligente que escolhe o modelo de IA apropriado baseado no tipo de usuário:

**Hermes Cliente:**
- Primary: DeepSeek
- Fallback: GLM 4.7 Flash
- Escopo: Acesso apenas ao tenant_id específico

**Hermes Admin Master:**
- Primary: GLM 4.7 (modelo mais inteligente)
- Fallback 1: GLM 4.7 Flash
- Fallback 2: DeepSeek (último recurso)
- Escopo: Acesso global a todos os tenants

### Integrações de Bot Telegram

O sistema suporta múltiplos bots Telegram com propósitos diferentes:

1. **TELEGRAM_BOT_TOKEN**: Bot padrão para clientes
2. **TELEGRAM_ADMIN_TOKEN**: Novo bot dedicado para Hermes Admin Master
3. **HERMES_MASTER_BOT_TOKEN**: Bot master existente (compatibilidade)

### Rotas Webhook

1. **/webhook/telegram**: Webhook padrão para clientes (existe)
2. **/webhook/telegram-admin**: Novo webhook para Hermes Admin Master
3. **/webhook/telegram-master**: Webhook para bot master existente

## Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# API Keys para LLMs
OPENROUTER_API_KEY=your_openrouter_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here

# Telegram Bots
TELEGRAM_BOT_TOKEN=your_client_bot_token
TELEGRAM_ADMIN_TOKEN=your_admin_bot_token
HERMES_MASTER_BOT_TOKEN=your_master_bot_token
HERMES_MASTER_BOT_USERNAME=your_master_bot_username
```

## Funcionalidades do Hermes Admin

### Comandos Disponíveis

O Hermes Admin Master pode responder a:

1. **Status do Sistema**
   - "status do sistema"
   - "resumo do dashboard"
   - "como estão os tenants"

2. **Listagem de Dados**
   - "listar clientes ativos"
   - "listar clientes bloqueados"
   - "listar módulos"

3. **Gerenciamento de Tarefas**
   - "criar tarefa: revisar pagamentos"
   - "listar tarefas abertas"
   - "marcar tarefa como concluída"

4. **Gerenciamento de Projetos**
   - "criar projeto: novo módulo"
   - "listar projetos ativos"

5. **Rotinas e Automação**
   - "criar rotina diária: backup"
   - "listar rotinas ativas"

6. **Memória do Sistema**
   - "salvar na memória: procedimento X"
   - "consultar memória"

7. **Logs e Auditoria**
   - "ver logs de ações"
   - "últimas ações do sistema"

8. **Análise de Projeto**
   - "analisar projeto"
   - "o que falta fazer"
   - "status da implementação"

9. **Skills**
   - "listar skills"
   - "executar skill: dashboard"
   - "criar nova skill"

### Integração com Painel Web

O Hermes Admin também está disponível no painel web em `/admin/hermes` com as seguintes funcionalidades:

- **Chat interativo** com Hermes Admin
- **Dashboard** com estatísticas do sistema
- **Gerenciamento de tarefas** administrativas
- **Gerenciamento de projetos**
- **Gerenciamento de rotinas**
- **Gerenciamento de memória**
- **Logs de ações**
- **Skills administrativas**

## Segurança

### Isolamento de Dados

- **Clientes**: Acesso apenas aos dados do próprio tenant
- **Admin Master**: Acesso global a todos os tenants
- **NUNCA** há mistura de dados entre tenants

### Autenticação

- Painel web: JWT token com validação de is_super_admin
- Telegram: Validação por token de bot secreto
- Webhooks: Header `X-Telegram-Bot-Api-Secret-Token`

## Comandos Úteis

### Configurar Webhook Telegram Admin

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN_ADMIN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-dominio.com/api/webhook/telegram-admin",
    "secret_token": "your_secret_token"
  }'
```

### Testar Hermes Admin via API

```bash
curl -X POST "https://seu-dominio.com/api/admin/hermes/chat" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "status do sistema"}'
```

### Ver Dashboard

```bash
curl -X GET "https://seu-dominio.com/api/admin/hermes/dashboard" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### Hermes Admin não responde

1. Verifique se `OPENROUTER_API_KEY` está configurada
2. Verifique se há um usuário com `is_super_admin=True`
3. Verifique logs do aplicativo: `logs/app.log`

### Telegram Admin não recebe mensagens

1. Verifique se `TELEGRAM_ADMIN_TOKEN` está correto
2. Verifique se o webhook está configurado
3. Verifique se o URL do webhook está acessível

### Erro de autorização no painel

1. Verifique se o usuário tem `is_super_admin=True`
2. Verifique se o token JWT é válido
3. Verifique se o tenant do usuário está ativo

## Monitoramento

O sistema gera logs detalhados:

- Uso de modelos de IA
- Fallbacks executados
- Erros de API
- Ações administrativas

Logs são salvos em `logs/app.log` com rotação automática.

## Performance

- DeepSeek: Rápido e econômico para clientes
- GLM 4.7: Mais inteligente para admin
- GLM 4.7 Flash: Rápido para fallback
- Sistema de fallback garante disponibilidade

## Futuras Melhorias

- [ ] Integração com Coolify para deploy
- [ ] Notificações push para admin
- [ ] Dashboard em tempo real
- [ ] Análise de uso de créditos
- [ ] Alertas automáticos
- [ ] Backup automático do sistema