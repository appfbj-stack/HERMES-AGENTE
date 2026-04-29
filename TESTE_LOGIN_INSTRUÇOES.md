# 🧪 TESTE DE LOGIN - INSTRUÇÕES

**Credenciais fornecidas:**
- Email: borgesjaf@gmail.com
- Senha: borges1972

---

## 📋 PASSO A PASSO PARA TESTAR O LOGIN

### 1. Testar login via navegador

1. Acesse: `https://meuchat.fbautomacao.space`
2. Preencha o formulário:
   - **Email da empresa / tenant:** (se necessário, o seu email de empresa)
   - **Email:** borgesjaf@gmail.com
   - **Senha:** borges1972
3. Clique em "Acessar painel"

### 2. Verificar erro no console do navegador

1. Aperte F12 para abrir DevTools
2. Vá para a aba "Console"
3. Tente fazer login novamente
4. Observe os erros:
   - **Se der erro de CORS:**
     - Mensagem: `Access to fetch at '...' has been blocked by CORS policy`
     - Solução: Configurar CORS_ORIGINS no backend
   - **Se der erro de rede:**
     - Mensagem: `NetworkError` ou `fetch failed`
     - Solução: Verificar se backend está rodando
   - **Se der erro 401:**
     - Mensagem: `Invalid credentials` ou `Unauthorized`
     - Solução: Verificar credenciais ou tenant inativo
   - **Se der erro 403:**
     - Mensagem: `Forbidden` ou `Tenant inactive`
     - Solução: Ativar tenant
   - **Se der erro 500:**
     - Mensagem: `Internal Server Error`
     - Solução: Verificar logs do backend

### 3. Verificar requisição de rede

1. Aperte F12 para abrir DevTools
2. Vá para a aba "Network"
3. Tente fazer login
4. Clique na requisição `/auth/login`
5. Verifique:
   - **Status Code:**
     - 200: Sucesso
     - 401: Credenciais inválidas
     - 403: Acesso negado (tenant inativo)
     - 500: Erro no servidor
   - **Response:**
     - Deve conter: `{"access_token": "...", "token_type": "bearer"}`
     - Se tiver erro: `{"detail": "mensagem de erro"}`

### 4. Verificar logs do backend

1. Acesse o Coolify
2. Vá para o serviço "hermes (localhost)"
3. Clique em "Logs"
4. Tente fazer login
5. Procure por:
   - `POST /auth/login` - A requisição chegou?
   - `Invalid credentials` - Credenciais inválidas?
   - `Tenant inactive` - Tenant inativo?
   - `Error` - Algum erro?

### 5. Testar via cURL

```bash
# Testar login com suas credenciais
curl -X POST https://api.meuchat.fbautomacao.space/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "borgesjaf@gmail.com",
    "password": "borges1972"
  }'
```

**Respostas possíveis:**

- **Sucesso:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

- **Credenciais inválidas:**
  ```json
  {
    "detail": "Invalid credentials"
  }
  ```

- **Tenant necessário:**
  ```json
  {
    "detail": "tenant_email is required for this user"
  }
  ```

### 6. Testar login com tenant (se necessário)

```bash
# Testar com tenant_email
curl -X POST https://api.meuchat.fbautomacao.space/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "borgesjaf@gmail.com",
    "password": "borges1972",
    "tenant_email": "seu-email-de-empresa@exemplo.com"
  }'
```

---

## 🔍 POSSÍVEIS PROBLEMAS E SOLUÇÕES

### Problema 1: Usuário não existe
**Solução:** Criar usuário via bootstrap ou diretamente no banco

### Problema 2: Senha incorreta
**Solução:** Resetar senha

### Problema 3: Tenant inativo
**Solução:** Ativar tenant no banco

### Problema 4: Múltiplos usuários com mesmo email
**Solução:** Especificar tenant_email no login

### Problema 5: Backend não está rodando
**Solução:** Verificar logs do backend e fazer redeploy

### Problema 6: CORS bloqueando
**Solução:** Configurar CORS_ORIGINS no Coolify

### Problema 7: JWT_SECRET não definido
**Solução:** Adicionar JWT_SECRET nas variáveis de ambiente

---

## 📊 CHECKLIST DE VERIFICAÇÃO

### Backend
- [ ] Backend está rodando?
- [ ] Health endpoint responde? (`https://api.meuchat.fbautomacao.space/health`)
- [ ] Login endpoint existe? (`https://api.meuchat.fbautomacao.space/auth/login`)
- [ ] JWT_SECRET está definido?
- [ ] CORS_ORIGINS está definido?
- [ ] Logs não mostram erros?

### Frontend
- [ ] Frontend está rodando?
- [ ] VITE_API_BASE_URL está correto?
- [ ] Console não mostra erros?
- [ ] Network requests funcionam?

### Banco de Dados
- [ ] Usuário existe?
- [ ] Senha está correta?
- [ ] Tenant existe?
- [ ] Tenant está ativo?

### Autenticação
- [ ] Credenciais estão corretas?
- [ ] Token está sendo gerado?
- [ ] Token está sendo salvo no localStorage?

---

## 🎯 PRÓXIMOS PASSOS

**Execute o teste de login e me informe:**

1. **Qual erro aparece no console do navegador?**
2. **Qual status code aparece na aba Network?**
3. **Qual erro aparece nos logs do backend?**
4. **Qual é a resposta do cURL?**

Com essas informações, posso identificar o problema exato e corrigir!

---

**Se quiser testar localmente:**

```bash
# Listar todos os usuários
python test_login.py --list-users

# Testar login
python test_login.py --email borgesjaf@gmail.com --password borges1972
```

**Se precisar especificar tenant:**

```bash
python test_login.py --email borgesjaf@gmail.com --password borges1972 --tenant-email seu-tenant@email.com
```
