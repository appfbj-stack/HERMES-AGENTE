# 🔧 TROUBLESHOOTING - PROBLEMAS DE LOGIN

**Data:** 29/04/2026
**Problema:** Login não funcionando
**Status:** Investigação em andamento

---

## 🔍 DIAGNÓSTICO INICIAL

### Sintomas:
- ❌ Login não funciona
- ❌ Usuário não consegue acessar o painel
- ❌ Token JWT expirando ou inválido

### Possíveis causas:

1. **CORS não configurado** ❌
   - Frontend não consegue comunicar com backend
   - Erro: `Access-Control-Allow-Origin`

2. **JWT_SECRET não definido** ❌
   - Token não pode ser gerado/validado
   - Erro: `Invalid token`

3. **Tenant inativo** ❌
   - Usuário existe mas tenant está inativo
   - Erro: `Tenant inactive`

4. **Senha incorreta** ❌
   - Senha não corresponde ao hash
   - Erro: `Invalid credentials`

5. **Token expirado** ❌
   - Token tem validade de 24h (config padrão)
   - Erro: `Invalid token`

---

## ✅ VERIFICAÇÕES NECESSÁRIAS

### 1. Verificar Variáveis de Ambiente

**No Coolify (Backend):**

```bash
DATABASE_URL=postgresql://...
JWT_SECRET=...  # ❌ IMPORTANTE: Deve estar definido
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=["https://meuchat.fbautomacao.space","https://api.meuchat.fbautomacao.space"]
```

**No Coolify (Frontend):**

```bash
VITE_API_BASE_URL=https://api.meuchat.fbautomacao.space
```

### 2. Verificar Status do Backend

**Testar rota de health:**
```bash
curl https://api.meuchat.fbautomacao.space/health
```

**Testar login:**
```bash
curl -X POST https://api.meuchat.fbautomacao.space/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@empresa.com",
    "password": "senha123",
    "tenant_email": "empresa@teste.com"
  }'
```

### 3. Verificar Logs do Backend

**No Coolify:**
1. Acessar serviço "hermes (localhost)"
2. Clicar em "Logs"
3. Procurar por erros relacionados a:
   - `CORS`
   - `JWT`
   - `Invalid credentials`
   - `Tenant inactive`

### 4. Verificar Logs do Frontend

**No navegador:**
1. Abrir DevTools (F12)
2. Vá para "Console"
3. Tentar fazer login
4. Verificar erros:
   - `CORS policy`
   - `Network error`
   - `401 Unauthorized`
   - `403 Forbidden`

---

## 🛠️ POSSÍVEIS SOLUÇÕES

### Solução 1: Configurar CORS

**Se o problema for CORS, adicionar no Coolify:**

```bash
CORS_ORIGINS=["https://meuchat.fbautomacao.space","https://api.meuchat.fbautomacao.space","http://localhost:5173"]
```

### Solução 2: Definir JWT_SECRET

**Se JWT_SECRET não estiver definido:**

```bash
JWT_SECRET=secreto-super-seguro-aleatorio-12345
```

### Solução 3: Ativar Tenant

**Se o tenant estiver inativo:**

```python
# Via Python shell no backend
from app.core.database import SessionLocal
from app.models import Tenant

db = SessionLocal()
tenant = db.query(Tenant).filter(Tenant.email == "empresa@teste.com").first()
if tenant:
    tenant.active = True
    db.commit()
db.close()
```

### Solução 4: Resetar Senha

**Se a senha estiver incorreta:**

```python
# Via Python shell no backend
from app.core.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.email == "admin@empresa.com").first()
if user:
    user.password = get_password_hash("nova_senha")
    db.commit()
db.close()
```

### Solução 5: Verificar Token

**Se o token expirou:**

```javascript
// No console do navegador
localStorage.clear()
location.reload()
```

---

## 🔬 ANÁLISE DO CÓDIGO ATUAL

### Backend (auth.py)

```python
# ✅ Login parece correto
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # 1. Busca tenant se tenant_email for fornecido
    # 2. Busca user
    # 3. Verifica senha
    # 4. Gera token
    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))
```

### Frontend (App.tsx)

```typescript
// ✅ Login parece correto
async function handleSubmit(event: FormEvent) {
  event.preventDefault();
  const result = await login(email, password, tenantEmail.trim() || undefined);
  localStorage.setItem("hermes_token", result.access_token);
  onLogged();
}
```

### Deps (get_current_user)

```python
# ✅ Autenticação parece correta
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == int(payload["sub"]), User.tenant_id == int(payload["tenant_id"])).first()
    return user
```

---

## 🎯 CHECKLIST PARA CORREÇÃO

- [ ] Verificar se JWT_SECRET está definido no backend
- [ ] Verificar se CORS_ORIGINS está definido corretamente
- [ ] Verificar se VITE_API_BASE_URL está correto no frontend
- [ ] Verificar se o tenant está ativo
- [ ] Verificar se a senha está correta
- [ ] Verificar logs do backend para erros
- [ ] Verificar logs do frontend para erros
- [ ] Testar login com curl
- [ ] Testar health endpoint
- [ ] Limpar localStorage e tentar novamente

---

## 📝 PRÓXIMOS PASSOS

1. **Coletar logs:**
   - Backend logs (Coolify)
   - Frontend console (Browser)
   - Network requests (Browser DevTools)

2. **Testar endpoints:**
   - `GET /health`
   - `POST /auth/login`

3. **Verificar envs:**
   - JWT_SECRET
   - CORS_ORIGINS
   - VITE_API_BASE_URL

4. **Verificar banco:**
   - Tenant ativo?
   - Usuário existe?
   - Senha correta?

---

**Status:** Aguardando logs do usuário para diagnóstico final

**Próximo ação:** Enviar checklist para o usuário verificar
