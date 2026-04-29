import { FormEvent, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  createCrmFollowup,
  createCrmLead,
  createCrmTask,
  connectCrmWhatsApp,
  deleteCrmLead,
  deleteCrmFollowup,
  deleteCrmTask,
  disconnectCrmWhatsApp,
  getChats,
  getAdminTenants,
  getCredits,
  getCrmConversations,
  getCrmDashboard,
  getCrmFollowups,
  getCrmKanban,
  getCrmLeadActivity,
  getCrmLeads,
  getCrmMessages,
  getCrmSettings,
  getCrmTasks,
  getCrmWhatsAppConnection,
  getCrmWhatsAppQrCode,
  getCrmWhatsAppStatus,
  getLeads,
  getMessages,
  getTasks,
  getHermesAdminDashboard,
  hermesAdminChat,
  login,
  me,
  moveCrmKanban,
  sendCrmConversationMessage,
  sendMessage,
  toggleAi,
  updateAdminTenantModules,
  updateCrmConversationState,
  updateCrmFollowup,
  updateCrmLead,
  updateCrmSettings,
  updateCrmTask,
  upsertCrmWhatsAppConnection,
} from "./api";
import CrmWorkspace from "./crm/CrmWorkspace";
import CrmKanbanPage from "./crm/KanbanPage";
import type {
  AdminTenant,
  Chat,
  Credit,
  CrmActivityLog,
  CrmConversation,
  CrmDashboard,
  CrmFollowup,
  CrmKanbanBoard,
  CrmLead,
  CrmMessage,
  CrmSettings,
  CrmTag,
  CrmTask,
  CrmWhatsAppConnection,
  CrmWhatsAppStatus,
  CreateTenantPayload,
  Lead,
  LoginResponse,
  MeResponse,
  Message,
  Task,
  HermesAdminChatResponse,
  HermesAdminDashboard,
  AdminTask,
  AdminProject,
  AdminRoutine,
  AdminMemory,
  AdminActionLog,
  AdminSkill,
  SkillSuggestion,
} from "./types";

function currencyCredits(credits?: Credit) {
  if (!credits) return "--";
  return `${credits.remaining}/${credits.total}`;
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function Layout({
  profile,
  children,
}: {
  profile: MeResponse;
  children: React.ReactNode;
}) {
  const location = useLocation();
  const navigate = useNavigate();

  const nav = [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Chat", path: "/chat" },
    ...(profile.modules.crm
      ? [
          { label: "CRM Dashboard", path: "/crm/dashboard" },
          { label: "CRM Leads", path: "/crm/leads" },
          { label: "CRM Kanban", path: "/crm/kanban" },
          { label: "CRM Conversas", path: "/crm/conversations" },
          { label: "CRM Follow-ups", path: "/crm/followups" },
          { label: "CRM Tarefas", path: "/crm/tasks" },
          { label: "CRM Config", path: "/crm/settings" },
        ]
      : []),
    ...(profile.modules.whatsapp ? [{ label: "WhatsApp", path: "/crm/whatsapp" }] : []),
    ...(profile.modules.kanban ? [{ label: "Kanban", path: "/crm/kanban" }] : []),
    ...(profile.modules.agenda ? [{ label: "Agenda", path: "/agenda" }] : []),
    ...(profile.modules.instagram ? [{ label: "Instagram", path: "/instagram" }] : []),
    ...(profile.modules.youtube ? [{ label: "YouTube", path: "/youtube" }] : []),
    ...(profile.modules.instagram || profile.modules.youtube ? [{ label: "Publicador", path: "/publisher" }] : []),
    ...(profile.user.is_super_admin ? [{ label: "Master", path: "/master" }] : []),
    { label: "Leads", path: "/leads" },
    { label: "Tarefas", path: "/tasks" },
    { label: "Créditos", path: "/credits" },
    { label: "Configurações", path: "/settings" },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#f7fbf6,transparent_35%),linear-gradient(135deg,#e2f2ea,#f4efe6)] text-ink">
      <div className="mx-auto flex min-h-screen max-w-[1520px]">
        <aside className="w-72 border-r border-black/5 bg-white/70 p-6 backdrop-blur-xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Hermes Agente</div>
            <h1 className="mt-2 font-serif text-3xl font-semibold">Painel SaaS</h1>
            <p className="mt-3 text-sm text-slate-600">{profile.tenant.name}</p>
          </div>

          <nav className="space-y-2">
            {nav.map((item) => {
              const active = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`w-full rounded-2xl px-4 py-3 text-left text-sm transition ${
                    active ? "bg-brand text-white shadow-soft" : "bg-white text-slate-700 hover:bg-brand/10"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-10 rounded-3xl bg-ink p-5 text-sm text-white">
            <div className="text-white/60">Operador</div>
            <div className="mt-2 font-medium">{profile.user.name}</div>
            <div className="text-white/70">{profile.user.role}</div>
            <div className="mt-4 text-xs uppercase tracking-[0.25em] text-white/50">
              CRM {profile.modules.crm ? "ativo" : "inativo"}
            </div>
          </div>
        </aside>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}

function LoginPage({ onLogged }: { onLogged: () => void }) {
  const [tenantEmail, setTenantEmail] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      console.log("Tentando login com:", { email, tenantEmail: tenantEmail.trim() || undefined, password: "***" });
      const result = await login(email, password, tenantEmail.trim() || undefined);
      console.log("Login bem-sucedido:", result);
      localStorage.setItem("hermes_token", result.access_token);
      onLogged();
    } catch (err) {
      console.error("Erro no login:", err);
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(140deg,#1b7f6b,#163b32_55%,#f1e9dc)] p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-[32px] bg-white p-8 shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Telegram + Hermes</div>
        <h1 className="mt-3 font-serif text-4xl font-semibold text-ink">Entrar</h1>
        <p className="mt-3 text-sm text-slate-500">Painel estilo chat com CRM, atendimento e operação multi-tenant.</p>
        <div className="mt-8 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Email</label>
            <input
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Senha</label>
            <input
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              type="password"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
              Email da empresa (opcional)
            </label>
            <input
              className="input"
              value={tenantEmail}
              onChange={(e) => setTenantEmail(e.target.value)}
              placeholder="empresa@email.com"
            />
            <p className="text-xs text-slate-400 mt-1">Preencha apenas se tiver múltiplos tenants</p>
          </div>
        </div>
        {error ? (
          <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
            <strong>Erro:</strong> {error}
            <div className="mt-2 text-xs text-red-500">
              Dica: Tente usar apenas o email e senha, sem o email da empresa.
            </div>
          </div>
        ) : null}
        <button
          disabled={loading}
          className="mt-6 w-full rounded-2xl bg-brand px-4 py-3 font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Entrando..." : "Acessar painel"}
        </button>
      </form>
    </div>
  );
}

function DashboardPage({ chats, credits, leads, tasks }: { chats: Chat[]; credits?: Credit; leads: Lead[]; tasks: Task[] }) {
  const cards = [
    { label: "Conversas", value: chats.length },
    { label: "Leads", value: leads.length },
    { label: "Tarefas", value: tasks.length },
    { label: "Créditos", value: currencyCredits(credits) },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div key={card.label} className="rounded-[28px] bg-white/80 p-6 shadow-soft backdrop-blur">
            <div className="text-sm text-slate-500">{card.label}</div>
            <div className="mt-3 text-4xl font-semibold text-ink">{card.value}</div>
          </div>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.4fr,1fr]">
        <div className="rounded-[32px] bg-white p-6 shadow-soft">
          <h2 className="font-serif text-2xl">Atividade recente</h2>
          <div className="mt-5 space-y-4">
            {chats.slice(0, 5).map((chat) => (
              <div key={chat.id} className="rounded-2xl bg-panel px-4 py-4">
                <div className="font-medium">{chat.contact_name || "Sem nome"}</div>
                <div className="text-sm text-slate-500">{chat.last_message || "Sem mensagens"}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-[32px] bg-ink p-6 text-white shadow-soft">
          <h2 className="font-serif text-2xl">Resumo operacional</h2>
          <div className="mt-5 space-y-4 text-sm text-white/80">
            <div>Plano: operação multi-tenant com créditos por mensagem.</div>
            <div>Canal: Telegram com resposta automática e atendimento humano.</div>
            <div>Estado: CRM integrado na base atual, em evolução por fases.</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatPage({
  chats,
  selectedChat,
  messages,
  onSelectChat,
  onSendMessage,
  onToggleAi,
}: {
  chats: Chat[];
  selectedChat?: Chat;
  messages: Message[];
  onSelectChat: (chat: Chat) => void;
  onSendMessage: (content: string) => Promise<void>;
  onToggleAi: () => Promise<void>;
}) {
  const [content, setContent] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    await onSendMessage(content);
    setContent("");
  }

  return (
    <div className="grid h-[calc(100vh-3rem)] gap-4 xl:grid-cols-[360px,1fr]">
      <section className="overflow-hidden rounded-[32px] bg-white shadow-soft">
        <div className="border-b border-black/5 p-5">
          <input className="input" placeholder="Buscar contatos" />
        </div>
        <div className="overflow-y-auto">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => onSelectChat(chat)}
              className={`flex w-full items-start gap-3 border-b border-black/5 px-5 py-4 text-left transition ${
                selectedChat?.id === chat.id ? "bg-brand/10" : "hover:bg-panel"
              }`}
            >
              <div className="mt-1 h-11 w-11 rounded-full bg-brand/20" />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{chat.contact_name || "Contato"}</span>
                  <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] uppercase text-emerald-700">
                    {chat.ai_paused ? "IA pausada" : "IA ativa"}
                  </span>
                </div>
                <div className="truncate text-sm text-slate-500">{chat.last_message || "Sem mensagens"}</div>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="flex flex-col overflow-hidden rounded-[32px] bg-[#efeae2] shadow-soft">
        {selectedChat ? (
          <>
            <div className="flex items-center justify-between border-b border-black/5 bg-white/90 px-6 py-4 backdrop-blur">
              <div>
                <div className="font-medium">{selectedChat.contact_name || "Contato"}</div>
                <div className="text-sm text-slate-500">
                  {selectedChat.ai_paused ? "Offline para IA" : "Online para IA"}
                </div>
              </div>
              <button onClick={onToggleAi} className="rounded-2xl bg-ink px-4 py-2 text-sm text-white">
                {selectedChat.ai_paused ? "Retomar IA" : "Pausar IA"}
              </button>
            </div>
            <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_right,rgba(27,127,107,0.10),transparent_25%),linear-gradient(180deg,#efeae2,#e7dfd3)] p-6">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`max-w-[70%] rounded-[22px] px-4 py-3 text-sm shadow ${
                      message.sender_type === "user"
                        ? "bg-white"
                        : message.sender_type === "assistant"
                          ? "ml-auto bg-bubble"
                          : "ml-auto bg-[#d8edff]"
                    }`}
                  >
                    {message.content}
                  </div>
                ))}
              </div>
            </div>
            <form onSubmit={handleSubmit} className="border-t border-black/5 bg-white/90 p-4 backdrop-blur">
              <div className="flex gap-3">
                <input
                  className="input flex-1"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Digite uma mensagem"
                />
                <button className="rounded-2xl bg-brand px-5 py-3 font-medium text-white">Enviar</button>
              </div>
            </form>
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center text-slate-500">Selecione uma conversa</div>
        )}
      </section>
    </div>
  );
}

function TablePage<T extends { id: number }>({
  title,
  rows,
  render,
}: {
  title: string;
  rows: T[];
  render: (row: T) => string[];
}) {
  return (
    <div className="rounded-[32px] bg-white p-6 shadow-soft">
      <h2 className="font-serif text-2xl">{title}</h2>
      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-b border-black/5">
                {render(row).map((cell, index) => (
                  <td key={index} className="px-3 py-4 text-slate-700">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CreditsPage({ credits }: { credits?: Credit }) {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="text-sm text-slate-500">Total</div>
        <div className="mt-3 text-4xl font-semibold">{credits?.total ?? 0}</div>
      </div>
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="text-sm text-slate-500">Usados</div>
        <div className="mt-3 text-4xl font-semibold">{credits?.used ?? 0}</div>
      </div>
      <div className="rounded-[32px] bg-ink p-6 text-white shadow-soft">
        <div className="text-sm text-white/60">Restantes</div>
        <div className="mt-3 text-4xl font-semibold">{credits?.remaining ?? 0}</div>
      </div>
    </div>
  );
}

function SettingsPage({ profile }: { profile: MeResponse }) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Tenant</h2>
        <div className="mt-5 space-y-3 text-sm text-slate-700">
          <div>Nome: {profile.tenant.name}</div>
          <div>Email: {profile.tenant.email}</div>
          <div>Plano: {profile.tenant.plan}</div>
        </div>
      </div>
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Operação</h2>
        <div className="mt-5 space-y-3 text-sm text-slate-700">
          <div>Canal primário: Telegram</div>
          <div>Engine IA: Hermes com fallback configurável.</div>
          <div>Módulo CRM: {profile.modules.crm ? "ativo" : "inativo"}</div>
        </div>
      </div>
    </div>
  );
}

// Old CrmWorkspace replaced by modular components (see crm/CrmWorkspace.tsx)
// Kept for reference only - now using CrmWorkspace.tsx with separate pages

function InstagramPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Instagram Integration</h2>
        <p className="mt-3 text-slate-600">Conecte e gerencie sua conta do Instagram Business.</p>
        
        <div className="mt-6 space-y-4">
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Conectar Conta</h3>
            <p className="mt-2 text-sm text-slate-600">Use o OAuth oficial do Meta para conectar sua conta.</p>
            <div className="mt-4 flex gap-3">
              <button 
                className="rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 text-sm font-semibold text-white hover:opacity-90"
              >
                <span className="mr-2">📷</span>
                Conectar Instagram
              </button>
              <button className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                Ver Contas Conectadas
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Funcionalidades</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li>✅ Publicar posts e Reels</li>
              <li>✅ Responder mensagens</li>
              <li>✅ Criar leads automaticamente</li>
              <li>✅ Integração com CRM</li>
              <li>✅ Responder via Hermes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function YouTubePage() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">YouTube Integration</h2>
        <p className="mt-3 text-slate-600">Conecte e gerencie seu canal do YouTube.</p>
        
        <div className="mt-6 space-y-4">
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Conectar Canal</h3>
            <p className="mt-2 text-sm text-slate-600">Use o OAuth oficial do Google para conectar seu canal.</p>
            <div className="mt-4 flex gap-3">
              <button 
                className="rounded-2xl bg-gradient-to-r from-red-500 to-red-600 px-6 py-3 text-sm font-semibold text-white hover:opacity-90"
              >
                <span className="mr-2">▶️</span>
                Conectar YouTube
              </button>
              <button className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                Ver Canais Conectados
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Funcionalidades</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              <li>✅ Publicar vídeos e Shorts</li>
              <li>✅ Capturar mensagens do live chat</li>
              <li>✅ Salvar conversas no CRM</li>
              <li>✅ Responder manual ou via Hermes</li>
              <li>✅ Criar leads automaticamente</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function ContentPublisherPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Publicador de Conteúdo</h2>
        <p className="mt-3 text-slate-600">Publique e agende conteúdo para Instagram e YouTube.</p>
        
        <div className="mt-6 space-y-4">
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Criar Publicação</h3>
            <p className="mt-2 text-sm text-slate-600">Selecione plataformas, faça upload de mídia e publique.</p>
            <div className="mt-4 flex gap-3">
              <button className="rounded-2xl bg-brand px-6 py-3 text-sm font-semibold text-white hover:bg-brand/90">
                <span className="mr-2">📤</span>
                Upload de Vídeo
              </button>
              <button className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                <span className="mr-2">📸</span>
                Upload de Imagem
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Histórico de Publicações</h3>
            <p className="mt-2 text-sm text-slate-600">Veja todas as publicações agendadas e publicadas.</p>
            <div className="mt-4 flex gap-3">
              <button className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                Ver Histórico
              </button>
            </div>
          </div>
          
          <div className="rounded-2xl bg-panel p-4">
            <h3 className="font-semibold text-slate-900">Plataformas Suportadas</h3>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded-xl border-2 border-purple-200 bg-purple-50 p-3 text-center">
                <div className="text-2xl">📷</div>
                <div className="text-sm font-semibold text-purple-900">Instagram</div>
                <div className="text-xs text-purple-700">Posts, Reels, Stories</div>
              </div>
              <div className="rounded-xl border-2 border-red-200 bg-red-50 p-3 text-center">
                <div className="text-2xl">▶️</div>
                <div className="text-sm font-semibold text-red-900">YouTube</div>
                <div className="text-xs text-red-700">Vídeos, Shorts, Lives</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AgendaPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Agenda</h2>
        <p className="mt-3 text-slate-600">Gerencie seus compromissos e agendamentos.</p>
        <div className="mt-6 rounded-2xl bg-panel p-4">
          <p className="text-sm text-slate-500">⚠️ Funcionalidade em desenvolvimento</p>
        </div>
      </div>
    </div>
  );
}

function HermesAdminChatPage({ profile }: { profile: MeResponse }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState<HermesAdminDashboard | null>(null);
  const [messages, setMessages] = useState<Array<{ id: string; sender: "user" | "assistant"; content: string }>>([
    {
      id: "welcome",
      sender: "assistant",
      content:
        "Olá, Fernando! Eu sou o Hermes Admin. Posso verificar status do sistema, módulos, erros, projeto e próximos passos.",
    },
  ]);

  useEffect(() => {
    getHermesAdminDashboard().then(setDashboard).catch(() => setDashboard(null));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const prompt = content.trim();
    if (!prompt || loading) return;

    const userMessage = { id: `${Date.now()}-user`, sender: "user" as const, content: prompt };
    setMessages((current) => [...current, userMessage]);
    setContent("");
    setLoading(true);
    setError("");

    try {
      const result = await hermesAdminChat(prompt);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          sender: "assistant",
          content: result.response,
        },
      ]);
      const nextDashboard = await getHermesAdminDashboard().catch(() => null);
      setDashboard(nextDashboard);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao falar com Hermes Admin");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid h-[calc(100vh-3rem)] gap-4 xl:grid-cols-[320px,1fr]">
      <section className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Super Admin</div>
        <h2 className="mt-2 font-serif text-3xl">Hermes Admin</h2>
        <p className="mt-3 text-sm text-slate-600">
          Chat operacional global do SaaS para {profile.user.name}.
        </p>

        <div className="mt-6 space-y-3 text-sm">
          <div className="rounded-2xl bg-panel p-4">
            <div className="text-slate-500">Clientes ativos</div>
            <div className="mt-1 text-2xl font-semibold text-ink">{dashboard?.active_tenants ?? "-"}</div>
          </div>
          <div className="rounded-2xl bg-panel p-4">
            <div className="text-slate-500">Clientes bloqueados</div>
            <div className="mt-1 text-2xl font-semibold text-ink">{dashboard?.blocked_tenants ?? "-"}</div>
          </div>
          <div className="rounded-2xl bg-panel p-4">
            <div className="text-slate-500">Tarefas abertas</div>
            <div className="mt-1 text-2xl font-semibold text-ink">{dashboard?.open_tasks ?? "-"}</div>
          </div>
        </div>

        <div className="mt-6 rounded-2xl bg-ink p-4 text-sm text-white">
          <div className="text-white/60">Comandos úteis</div>
          <div className="mt-2">status do sistema</div>
          <div>listar módulos</div>
          <div>ver erros</div>
          <div>analisar projeto</div>
          <div>o que falta fazer</div>
        </div>
      </section>

      <section className="flex flex-col overflow-hidden rounded-[32px] bg-[#efeae2] shadow-soft">
        <div className="border-b border-black/5 bg-white/90 px-6 py-4 backdrop-blur">
          <div className="font-medium">Hermes Super Admin</div>
          <div className="text-sm text-slate-500">Acesso global ao sistema</div>
        </div>

        <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_right,rgba(27,127,107,0.10),transparent_25%),linear-gradient(180deg,#efeae2,#e7dfd3)] p-6">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[80%] whitespace-pre-wrap rounded-[22px] px-4 py-3 text-sm shadow ${
                  message.sender === "user" ? "bg-white" : "ml-auto bg-bubble"
                }`}
              >
                {message.content}
              </div>
            ))}
            {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="border-t border-black/5 bg-white/90 p-4 backdrop-blur">
          <div className="flex gap-3">
            <input
              className="input flex-1"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Pergunte sobre status, módulos, erros ou projeto"
            />
            <button
              disabled={loading}
              className="rounded-2xl bg-brand px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Enviando..." : "Enviar"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function CrmWhatsAppPage() {
  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">WhatsApp CRM</h2>
        <p className="mt-3 text-slate-600">A conexão do WhatsApp CRM está disponível no backend atual e a tela dedicada ainda precisa ser refinada.</p>
        <div className="mt-6 rounded-2xl bg-panel p-4">
          <p className="text-sm text-slate-500">Use o módulo CRM e as integrações existentes enquanto a interface específica é finalizada.</p>
        </div>
      </div>
    </div>
  );
}

function MasterPage({ profile }: { profile: MeResponse }) {
  const [tenants, setTenants] = useState<AdminTenant[]>([]);
  const [savingTenantId, setSavingTenantId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function loadTenants() {
    try {
      setTenants(await getAdminTenants());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar tenants");
    }
  }

  useEffect(() => {
    if (!profile.user.is_super_admin) return;
    loadTenants();
  }, [profile.user.is_super_admin]);

  if (!profile.user.is_super_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-[linear-gradient(135deg,#2a1f43,#3d2d63_55%,#e6d7b7)] p-8 text-white shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-white/60">Admin Master</div>
        <h2 className="mt-3 font-serif text-4xl">Módulos por cliente</h2>
        <p className="mt-3 max-w-2xl text-sm text-white/75">
          Controle central para ativar ou desativar o CRM por tenant sem expor dados de um cliente para outro.
        </p>
      </div>

      {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}

        <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="flex items-center justify-between gap-4">
          <h3 className="font-serif text-2xl">Tenants</h3>
          <div className="text-sm text-slate-500">{tenants.length} clientes</div>
        </div>
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
              <th className="px-3 py-3 font-medium">Tenant</th>
              <th className="px-3 py-3 font-medium">Plano</th>
              <th className="px-3 py-3 font-medium">Status</th>
              <th className="px-3 py-3 font-medium">CRM</th>
              <th className="px-3 py-3 font-medium">WhatsApp</th>
              <th className="px-3 py-3 font-medium">Kanban</th>
              <th className="px-3 py-3 font-medium">Agenda</th>
              <th className="px-3 py-3 font-medium">Instagram</th>
              <th className="px-3 py-3 font-medium">YouTube</th>
              <th className="px-3 py-3 font-medium">Content Publisher</th>
              <th className="px-3 py-3 font-medium">Criado em</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr key={tenant.id} className="border-t border-black/5">
                  <td className="px-3 py-4">
                    <div className="font-medium text-ink">{tenant.name}</div>
                    <div className="text-slate-500">{tenant.email}</div>
                  </td>
                  <td className="px-3 py-4 text-slate-700">{tenant.plan}</td>
                  <td className="px-3 py-4">
                    <span className={`rounded-full px-3 py-1 text-xs ${tenant.active ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
                      {tenant.active ? "ativo" : "inativo"}
                    </span>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.crm_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { crm: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.crm_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.whatsapp_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { whatsapp: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.whatsapp_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.kanban_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { kanban: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.kanban_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.agenda_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { agenda: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.agenda_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.instagram_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { instagram: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.instagram_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.youtube_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { youtube: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.youtube_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.content_publisher_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={async (event) => {
                          setSavingTenantId(tenant.id);
                          setError("");
                          try {
                            const updated = await updateAdminTenantModules(tenant.id, { content_publisher: event.target.checked });
                            setTenants((current) =>
                              current.map((item) => (item.id === updated.id ? updated : item)),
                            );
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
                          } finally {
                            setSavingTenantId(null);
                          }
                        }}
                      />
                      <span className="text-slate-700">{tenant.content_publisher_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4 text-slate-700">{formatDateTime(tenant.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ProtectedApp() {
  const [profile, setProfile] = useState<MeResponse | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [credits, setCredits] = useState<Credit>();

  useEffect(() => {
    Promise.all([me(), getChats(), getLeads(), getTasks(), getCredits()])
      .then(([profileData, chatsData, leadsData, tasksData, creditsData]) => {
        setProfile(profileData);
        setChats(chatsData);
        setLeads(leadsData);
        setTasks(tasksData);
        setCredits(creditsData);
        if (chatsData.length > 0) {
          setSelectedChatId(chatsData[0].id);
        }
      })
      .catch(() => {
        localStorage.removeItem("hermes_token");
        window.location.href = "/";
      });
  }, []);

  useEffect(() => {
    if (!selectedChatId) return;
    getMessages(selectedChatId).then(setMessages).catch(() => setMessages([]));
  }, [selectedChatId]);

  async function refreshChats() {
    const data = await getChats();
    setChats(data);
  }

  if (!profile) {
    return <div className="flex min-h-screen items-center justify-center">Carregando...</div>;
  }

  const selectedChat = chats.find((item) => item.id === selectedChatId);

  return (
    <Layout profile={profile}>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage chats={chats} credits={credits} leads={leads} tasks={tasks} />} />
        <Route
          path="/chat"
          element={
            profile.user.is_super_admin ? (
              <HermesAdminChatPage profile={profile} />
            ) : (
              <ChatPage
                chats={chats}
                selectedChat={selectedChat}
                messages={messages}
                onSelectChat={(chat) => setSelectedChatId(chat.id)}
                onSendMessage={async (content) => {
                  if (!selectedChat) return;
                  await sendMessage(selectedChat.id, content);
                  const items = await getMessages(selectedChat.id);
                  setMessages(items);
                  await refreshChats();
                  setCredits(await getCredits());
                }}
                onToggleAi={async () => {
                  if (!selectedChat) return;
                  await toggleAi(selectedChat.id, !selectedChat.ai_paused);
                  await refreshChats();
                }}
              />
            )
          }
        />
        <Route path="/crm" element={<CrmWorkspace profile={profile} />} />
        <Route path="/crm/whatsapp" element={<CrmWhatsAppPage />} />
        <Route path="/crm/kanban" element={<CrmKanbanPage />} />
        <Route path="/agenda" element={<AgendaPage />} />
        <Route path="/instagram" element={<InstagramPage />} />
        <Route path="/youtube" element={<YouTubePage />} />
        <Route path="/publisher" element={<ContentPublisherPage />} />
        <Route path="/master" element={<MasterPage profile={profile} />} />
        <Route path="/leads" element={<TablePage title="Leads" rows={leads} render={(row) => [row.name, row.phone || "-", row.interest || "-", row.status]} />} />
        <Route path="/tasks" element={<TablePage title="Tarefas" rows={tasks} render={(row) => [row.title, row.description || "-", row.status, row.due_date || "-"]} />} />
        <Route path="/credits" element={<CreditsPage credits={credits} />} />
        <Route path="/settings" element={<SettingsPage profile={profile} />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem("hermes_token")));

  if (!authenticated) {
    return <LoginPage onLogged={() => setAuthenticated(true)} />;
  }

  return <ProtectedApp />;
}
