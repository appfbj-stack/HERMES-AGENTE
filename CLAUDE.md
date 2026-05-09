# HERMES AGENTE — Contexto Completo do Projeto

> Arquivo de referencia para o Claude. Leia isso no inicio de cada sessao sobre este projeto.

---

## VISAO DO PRODUTO

SaaS multi-tenant de assistente inteligente + CRM. Dois produtos separados:

1. **Apps de nicho** (independentes): mecanica.fbautomacao.space, fotografia.fbautomacao.space
2. **Hermes SaaS** (CRM + Chat + IA): meuchat.fbautomacao.space — produto principal que Fernando vende

O Hermes SaaS e vendido por modulos:
- Cada cliente (tenant) compra acesso a modulos separados: CRM, Kanban, WhatsApp, Instagram, YouTube, Agenda
- Super Admin ve todos os clientes, pode bloquear, ativar modulos, gerenciar creditos

---

## ARQUITETURA

- Frontend: React/Vite/TypeScript/Tailwind -> meuchat.fbautomacao.space
- Backend: FastAPI (Python) -> meuchat.fbautomacao.space/api
- Banco: PostgreSQL + Redis
- Deploy: Coolify no servidor 187.77.229.227:8000

Projeto Coolify: "hermes agente" > production > application "hermes"
URL Coolify: http://187.77.229.227:8000/project/njrazdd45aqaqvpij3yfaubu/environment/w9mnqp422rkr9ou9ut0bx423/application/zrjij5228iruj3pcrvrjijiw

---

## REPOSITORIO

GitHub: https://github.com/appfbj-stack/HERMES-AGENTE

backend/app/
  main.py          - startup, migrations automaticas, ensure_env_super_admin
  models.py        - SQLAlchemy models
  schemas.py       - Pydantic schemas (MeResponse, TenantModulesOut)
  deps.py          - get_current_user, get_current_modules
  routes/
    auth.py        - /auth/login, /auth/me
    admin.py       - /admin/* (super admin only)
    admin_hermes.py - /admin/hermes/* (Hermes Admin AI)
    crm.py         - /crm/*
    integrations.py - Instagram, YouTube, WhatsApp
    public.py      - /public/chat/{tenant_id}
  services/modules.py - build_modules_out(), module_enabled()

frontend/src/
  App.tsx          - Main app, rotas, toda logica de estado
  MasterPanel.tsx  - Painel super admin (gestao de tenants)
  PublicChat.tsx   - Chat publico sem login
  api.ts           - Todas chamadas de API
  crm/             - Modulos CRM (Workspace, Kanban)

---

## USUARIOS E TENANTS NO BANCO

Usuarios (tabela users):
  id=1  borgesjaf@gmail.com         admin  is_super_admin=TRUE
  id=3  fernandojaborges@gmail.com  admin  is_super_admin=TRUE  <- Fernando!
  id=4  admin@mecanica.com          admin  is_super_admin=false
  id=5  admin@fotografia.com        admin  is_super_admin=false

Tenants:
  id=7  Hermes           active=true
  id=8  Admin Master     active=true
  id=9  Auto Center Mecanica  active=true
  id=10 Estudio de Fotografia active=true

Modulos: TODOS os tenants tem tudo ativo
  crm=T, whatsapp=T, whatsapp_evolution=T, instagram=T, youtube=T, kanban=T, agenda=T

---

## ACESSO AO SISTEMA

Super Admin (Hermes Admin Chat + Master Panel):
  URL: https://meuchat.fbautomacao.space/login
  Email: fernandojaborges@gmail.com (ou borgesjaf@gmail.com)
  Tela Chat: mostra Hermes Admin (IA operacional)
  Menu extra: "Master" aparece

Admin Fotografia:
  Email: admin@fotografia.com
  Tenant: Estudio de Fotografia (id=10)
  ATENCAO: is_super_admin=false -> Chat mostra "HERMES CLIENTE" normal

Admin Mecanica:
  Email: admin@mecanica.com
  Tenant: Auto Center Mecanica (id=9)

---

## SISTEMA DE MODULOS

Tabela tenant_modules (um row por tenant).
Frontend: menu lateral dinamico baseado em profile.modules.
  crm -> CRM Dashboard, Leads, Kanban, Conversas, Follow-ups, Tarefas
  whatsapp -> WhatsApp
  agenda -> Agenda
  instagram + youtube + content_publisher -> integracao de conteudo
  is_super_admin -> Chat mostra Hermes Admin em vez do chat normal

---

## HERMES ADMIN (Super Admin Chat)

Aparece na rota /chat APENAS para usuarios com is_super_admin=true.
Componente: HermesAdminChatPage em App.tsx
API: POST /api/admin/hermes/chat, GET /api/admin/hermes/dashboard
Comandos rapidos: "status do sistema", "listar modulos", "ver erros"

---

## OUTROS APPS (independentes do Hermes SaaS)

App Mecanica:
  URL: https://mecanica.fbautomacao.space
  Repo: appfbj-stack/controle-de-oficina (TypeScript)
  Coolify: projeto "app mecanica"

App Fotografia:
  URL: https://fotografia.fbautomacao.space
  Repo: appfbj-stack/foto-agenda-v1 -> arquivo principal: App.tsx
  Coolify: projeto "foto agenda"
  Ultimo commit: 829fb6e (toggles CSS sliding)

---

## PROBLEMAS CONHECIDOS / HISTORICO

Chat super admin "sumiu":
  Causa: Usuario logado como admin@fotografia.com (is_super_admin=false)
  Solucao: Fazer login com fernandojaborges@gmail.com

Toggles admin panel Fotografia:
  Status: RESOLVIDO - commit 829fb6e

Modulos WhatsApp/Instagram/YouTube:
  Status: Todos ja ativos para todos os tenants

---

## ROADMAP PENDENTE

- Corrigir Hermes Agente: salvar tarefas/lembretes/memoria no banco
- Verificar integracoes WhatsApp Evolution e Telegram
- Adicionar logs e try/catch global
- Chat estilo WhatsApp web para super admin ver todas conversas dos clientes separados
- Vender modulos separados por assinatura

---

## VISAO FUTURA (PRD)

Fernando quer vender o Hermes SaaS onde:
- Super Admin ve TODOS os clientes em lista (igual WhatsApp Web) e pode bloquear
- Cada cliente tem seu proprio Hermes isolado
- Modulos vendidos separados: CRM, Kanban, WhatsApp, Instagram, YouTube
- Creditos por mensagem
- Suporte a Telegram + WhatsApp (Evolution API)
- Integracao futura: Asaas (pagamentos), Chatwoot, multi-agente
