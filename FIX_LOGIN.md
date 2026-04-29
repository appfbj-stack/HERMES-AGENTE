# ⚠️ PROBLEMAS DE LOGIN IDENTIFICADOS E SOLUÇÕES

**Data:** 29/04/2026
**Última atualização:** Commit 37f4b7a
**Status:** ⚠️ Login pode não estar funcionando devido a configurações

---

## 🔴 PROBLEMAS ENCONTRADOS

### 1. ❌ Deploy recente (Commit 37f4b7a)
**Problema:** Adição do Git ao Dockerfile do backend pode ter causado problemas no deploy.

**Solução:**
- Verificar se o backend iniciou corretamente após o deploy
- Checar logs do backend no Coolify
- Se necessário, fazer redeploy

### 2. ❌ Variáveis de ambiente podem não estar definidas
**Problema:** JWT_SECRET ou CORS_ORIGINS podem não estar configurados no Coolify.

**Solução:**
- Verificar variáveis de ambiente no Coolify
- Adicionar JWT_SECRET se não existir
- Adicionar CORS_ORIGINS se não existir

### 3. ❌ Token JWT expirando
**Problema:** Token tem validade de 1440 minutos (24h), mas pode estar expirando antes.

**Solução:**
- Limpar localStorage no navegador
- Fazer login novamente

---

## ✅ CONFIGURAÇÕES NECESSÁRIAS

### Backend (Coolify)

```bash
# Obrigatórias
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=secreto-super-seguro-aleatorio-1234567890

# Recomendadas
CORS_ORIGINS=["https://meuchat.fbautomacao.space","https://api.meuchat.fbautomacao.space"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BOOTSTRAP_TOKEN=hermes-bootstrap

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=...
HERMES_MASTER_BOT_TOKEN=...
HERMES_MASTER_BOT_USERNAME=...

# AI (opcional)
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MODEL=deepseek/deepseek-chat

# Redis (opcional)
REDIS_URL=redis://redis:6379/0

# Asaas (opcional)
ASAAS_API_KEY=...
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
ASAAS_WEBHOOK_TOKEN=...
ASAAS_OVERDUE_GRACE_DAYS=7

# Coolify (opcional)
COOLIFY_API_BASE_URL=...
COOLIFY_API_KEY=...

# GitHub (opcional)
GITHUB_TOKEN=...
GITHUB_OWNER=...
GITHUB_REPO=...

# Admin Telegram (opcional)
ADMIN_TELEGRAM_ID=...

# Logs
LOG_LEVEL=INFO
```

### Frontend (Coolify)

```bash
# Obrigatórias
VITE_API_BASE_URL=https://api.meuchat.fbautomacao.space
```

---

## 🔧 COMO CORRIGIR O LOGIN

### Passo 1: Verificar logs do backend

1. Acessar Coolify
2. Ir para serviço "hermes (localhost)"
3. Clicar em "Logs"
4. Procurar por erros:
   - `Error`
   - `Exception`
   - `Failed`
   - `JWT`
   - `CORS`

### Passo 2: Verificar variáveis de ambiente

1. Acessar Coolify
2. Ir para serviço "hermes (localhost)"
3. Clicar em "Configuration"
4. Verificar se JWT_SECRET está definido
5. Verificar se CORS_ORIGINS está definido

### Passo 3: Testar login manualmente

```bash
# Testar health endpoint
curl https://api.meuchat.fbautomacao.space/health

# Testar login
curl -X POST https://api.meuchat.fbautomacao.space/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seu@email.com",
    "password": "sua_senha",
    "tenant_email": "empresa@teste.com"
  }'
```

### Passo 4: Limpar cache do navegador

1. Abrir DevTools (F12)
2. Ir para "Application"
3. Clicar em "Local Storage"
4. Selecionar o domínio
5. Limpar o valor "hermes_token"
6. Recarregar a página

### Passo 5: Verificar console do navegador

1. Abrir DevTools (F12)
2. Ir para "Console"
3. Tentar fazer login
4. Verificar erros:
   - `CORS policy`
   - `Network error`
   - `401 Unauthorized`
   - `403 Forbidden`

### Passo 6: Verificar network requests

1. Abrir DevTools (F12)
2. Ir para "Network"
3. Tentar fazer login
4. Clicar na requisição `/auth/login`
5. Verificar:
   - Status code (200 = ok, 401 = unauthorized, 403 = forbidden)
   - Response
   - Headers

---

## 📋 CHECKLIST PARA CORREÇÃO DO LOGIN

### Backend
- [ ] Backend está rodando?
- [ ] JWT_SECRET está definido?
- [ ] CORS_ORIGINS está definido?
- [ ] DATABASE_URL está correto?
- [ ] Logs não mostram erros?
- [ ] Health endpoint responde?

### Frontend
- [ ] Frontend está rodando?
- [ ] VITE_API_BASE_URL está correto?
- [ ] Build foi feito corretamente?
- [ ] Console não mostra erros?
- [ ] Network requests funcionam?

### Banco de Dados
- [ ] Tenant existe?
- [ ] Tenant está ativo?
- [ ] Usuário existe?
- [ ] Senha está correta?

### Autenticação
- [ ] Token está sendo gerado?
- [ ] Token está sendo salvo no localStorage?
- [ ] Token está sendo enviado nas requisições?
- [ ] Token não está expirado?

---

## 🎯 AÇÕES IMEDIATAS

### 1. Se backend não está rodando:
```bash
# No Coolify, clicar em "Redeploy"
# Aguardar deploy completar
# Verificar logs
```

### 2. Se JWT_SECRET não está definido:
```bash
# No Coolify, adicionar variável:
JWT_SECRET=secreto-super-seguro-aleatorio-1234567890
# Redeploy
```

### 3. Se CORS_ORIGINS não está definido:
```bash
# No Coolify, adicionar variável:
CORS_ORIGINS=["https://meuchat.fbautomacao.space","https://api.meuchat.fbautomacao.space"]
# Redeploy
```

### 4. Se token está expirado:
```bash
# No navegador, console:
localStorage.clear()
location.reload()
```

### 5. Se usuário ou senha estão incorretos:
```python
# Resetar senha via Python shell
from app.core.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.email == "seu@email.com").first()
if user:
    user.password = get_password_hash("nova_senha")
    db.commit()
    print("Senha resetada!")
else:
    print("Usuário não encontrado!")
db.close()
```

### 6. Se tenant está inativo:
```python
# Ativar tenant via Python shell
from app.core.database import SessionLocal
from app.models import Tenant

db = SessionLocal()
tenant = db.query(Tenant).filter(Tenant.email == "empresa@teste.com").first()
if tenant:
    tenant.active = True
    db.commit()
    print("Tenant ativado!")
else:
    print("Tenant não encontrado!")
db.close()
```

---

## 📞 SUPORTE

Se o problema persistir após verificar todos os itens acima:

1. Coletar logs do backend
2. Coletar logs do frontend (console)
3. Coletar network requests
4. Verificar variáveis de ambiente
5. Enviar informações para análise

---

**Status:** ⚠️ Aguardando feedback do usuário sobre logs e erros

**Próximo passo:** Usuário deve verificar logs e fornecer informações
