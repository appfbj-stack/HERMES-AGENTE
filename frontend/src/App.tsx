import { FormEvent, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  activateClientSkill,
  createCrmFollowup,
  createCrmLead,
  createCrmTask,
  getClientProfile,
  getClientSkills,
  getClientSuggestions,
  connectCrmWhatsApp,
  deleteCrmLead,
  deleteCrmFollowup,
  deleteCrmTask,
  deleteIntegrationPost,
  disconnectIntegrationAccount,
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
  getIntegrationAccounts,
  getIntegrationPosts,
  getIntegrationStats,
  getTenantModules,
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
  startInstagramConnect,
  startYouTubeConnect,
  toggleAi,
  toggleClientSkill,
  updateAdminTenantModules,
  updateClientProfile,
  updateCrmConversationState,
  updateCrmFollowup,
  updateCrmLead,
  updateCrmSettings,
  updateCrmTask,
  upsertCrmWhatsAppConnection,
  createIntegrationPost,
  publishIntegrationPost,
  getAgendaReminders,
  getAgendaAppointments,
  updateAgendaReminder,
  updateAgendaAppointment,
} from "./api";
import CrmWorkspace from "./crm/CrmWorkspace";
import CrmKanbanPage from "./crm/KanbanPage";
import PastoralWorkspace from "./pastoral/PastoralWorkspace";
import type {
  AdminTenant,
  Chat,
  ClientProfile,
  ClientSkill,
  ClientSuggestion,
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
  SocialIntegrationAccount,
  SocialIntegrationStats,
  SocialPost,
  AgentReminder,
  AgentAppointment,
} from "./types";

function currencyCredits(credits?: Credit) {
  if (!credits) return "--";
  return `${credits.remaining}/${credits.total}`;
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function parseAutomationLines(content: string) {
  const lines = content.split("\n").map((line) => line.trim()).filter(Boolean);
  const automationLines: string[] = [];
  const bodyLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("✅") || line.startsWith("⏰")) {
      automationLines.push(line);
    } else {
      bodyLines.push(line);
    }
  }

  return {
    automationLines,
    body: bodyLines.join("\n"),
  };
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
  const modules = profile.modules;

  const nav = [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Chat", path: "/chat" },
    ...(modules.crm
      ? [
          { label: "CRM Dashboard", path: "/crm/dashboard" },
          { label: "CRM Leads", path: "/crm/leads" },
          ...(modules.kanban ? [{ label: "CRM Kanban", path: "/crm/kanban" }] : []),
          { label: "CRM Conversas", path: "/crm/conversations" },
          { label: "CRM Follow-ups", path: "/crm/followups" },
          { label: "CRM Tarefas", path: "/crm/tasks" },
          { label: "CRM Config", path: "/crm/settings" },
        ]
      : []),
    ...(modules.whatsapp_evolution ? [{ label: "WhatsApp", path: "/crm/whatsapp" }] : []),
    ...(modules.crm && modules.agenda ? [{ label: "Agenda", path: "/agenda" }] : []),
    ...(modules.instagram ? [{ label: "Instagram", path: "/instagram" }] : []),
    ...(modules.youtube ? [{ label: "YouTube", path: "/youtube" }] : []),
    ...(modules.content_publisher ? [{ label: "Publicador", path: "/publisher" }] : []),
    ...(modules.agenda_pastoral ? [{ label: "⛪ Pastoral", path: "/pastoral" }] : []),
    ...(profile.user.is_super_admin ? [{ label: "Master", path: "/master" }] : []),
    ...(modules.crm ? [{ label: "Leads", path: "/leads" }, { label: "Tarefas", path: "/tasks" }] : []),
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
            <button
              onClick={() => { localStorage.removeItem("hermes_token"); navigate("/login"); }}
              className="mt-4 w-full rounded-xl bg-white/10 py-2 text-xs font-semibold text-white/80 hover:bg-white/20 transition-all"
            >
              Sair
            </button>
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
      localStorage.removeItem("hermes_token");
      const result = await login(email.trim(), password, tenantEmail.trim() || undefined);
      localStorage.setItem("hermes_token", result.access_token);
      onLogged();
    } catch (err) {
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
              autoComplete="username"
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
              autoComplete="current-password"
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
            {error.includes("mais de uma empresa") ? (
              <div className="mt-2 text-xs text-red-500">
                Use o campo "Email da empresa" com o email do tenant correto.
              </div>
            ) : error.includes("Email da empresa não encontrado") ? (
              <div className="mt-2 text-xs text-red-500">
                Revise o email da empresa ou tente entrar só com email e senha.
              </div>
            ) : error.includes("Tenant inactive") ? (
              <div className="mt-2 text-xs text-red-500">
                Esse tenant está inativo. Reative no painel master antes de tentar novamente.
              </div>
            ) : (
              <div className="mt-2 text-xs text-red-500">
                Tente usar apenas o email e senha, sem o email da empresa, se esse login existir em um único tenant.
              </div>
            )}
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

function DashboardPage({
  chats,
  credits,
  leads,
  tasks,
  clientProfile,
  clientSkills,
  clientSuggestions,
}: {
  chats: Chat[];
  credits?: Credit;
  leads: Lead[];
  tasks: Task[];
  clientProfile: ClientProfile | null;
  clientSkills: ClientSkill[];
  clientSuggestions: ClientSuggestion[];
}) {
  const cards = [
    { label: "Conversas", value: chats.length },
    { label: "Leads", value: leads.length },
    { label: "Tarefas", value: tasks.length },
    { label: "Créditos", value: currencyCredits(credits) },
  ];
  const recentTasks = [...tasks]
    .sort((a, b) => {
      const dateA = a.due_date ? new Date(a.due_date).getTime() : new Date(a.created_at).getTime();
      const dateB = b.due_date ? new Date(b.due_date).getTime() : new Date(b.created_at).getTime();
      return dateA - dateB;
    })
    .slice(0, 5);

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
          <h2 className="font-serif text-2xl">Lembretes do Hermes</h2>
          <div className="mt-5 space-y-4 text-sm text-white/80">
            {recentTasks.length > 0 ? (
              recentTasks.map((task) => (
                <div key={task.id} className="rounded-2xl bg-white/10 px-4 py-3">
                  <div className="font-medium text-white">{task.title}</div>
                  <div className="text-xs text-white/70">
                    {task.due_date ? `Vencimento ${formatDateTime(task.due_date)}` : `Criada em ${formatDateTime(task.created_at)}`}
                  </div>
                </div>
              ))
            ) : (
              <>
                <div>Nenhum lembrete ou tarefa recente criado pelo Hermes.</div>
                <div>Exemplo: “me lembre de ajustar o CRM amanhã às 8”.</div>
              </>
            )}
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
  clientProfile,
  clientSuggestions,
  clientSkills,
  onSelectChat,
  onSendMessage,
  onToggleAi,
}: {
  chats: Chat[];
  selectedChat?: Chat;
  messages: Message[];
  clientProfile: ClientProfile | null;
  clientSuggestions: ClientSuggestion[];
  clientSkills: ClientSkill[];
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
        <div className="border-b border-black/5 bg-panel/60 px-5 py-4">
          <div className="text-xs uppercase tracking-[0.25em] text-slate-400">Hermes Cliente</div>
          <div className="mt-2 text-sm text-slate-700">
            {clientProfile?.tipo_negocio || "Perfil ainda não definido"} • automação {clientProfile?.nivel_automacao || "medio"}
          </div>
          <div className="mt-2 text-xs text-slate-500">
            {clientSuggestions.filter((item) => !item.active).length > 0
              ? `${clientSuggestions.filter((item) => !item.active).length} sugestão(ões) aguardando confirmação`
              : `${clientSkills.filter((item) => item.ativa).length} skill(s) ativa(s)`}
          </div>
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
                    {(() => {
                      const parsed = parseAutomationLines(message.content);
                      return (
                        <div className="space-y-2">
                          {parsed.automationLines.map((line, index) => (
                            <div
                              key={`${message.id}-auto-${index}`}
                              className="rounded-2xl bg-black/5 px-3 py-2 text-xs font-semibold text-slate-700"
                            >
                              {line}
                            </div>
                          ))}
                          {parsed.body ? <div className="whitespace-pre-wrap">{parsed.body}</div> : null}
                        </div>
                      );
                    })()}
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
  const [clientProfile, setClientProfile] = useState<ClientProfile | null>(null);
  const [clientSkills, setClientSkills] = useState<ClientSkill[]>([]);
  const [clientSuggestions, setClientSuggestions] = useState<ClientSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({
    tipo_negocio: "",
    objetivo: "",
    horario_funcionamento: "",
    preferencias: "",
    nivel_automacao: "medio",
  });

  async function loadClientHermes() {
    setLoading(true);
    setError("");
    try {
      const [profileData, skillsData, suggestionsData] = await Promise.all([
        getClientProfile(),
        getClientSkills(),
        getClientSuggestions(),
      ]);
      setClientProfile(profileData);
      setClientSkills(skillsData);
      setClientSuggestions(suggestionsData);
      setForm({
        tipo_negocio: profileData.tipo_negocio || "",
        objetivo: profileData.objetivo || "",
        horario_funcionamento: profileData.horario_funcionamento || "",
        preferencias: profileData.preferencias || "",
        nivel_automacao: profileData.nivel_automacao || "medio",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar configurações do Hermes Cliente");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadClientHermes();
  }, []);

  async function handleSaveProfile(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await updateClientProfile({
        tipo_negocio: form.tipo_negocio || null,
        objetivo: form.objetivo || null,
        horario_funcionamento: form.horario_funcionamento || null,
        preferencias: form.preferencias || null,
        nivel_automacao: form.nivel_automacao,
      });
      setClientProfile(updated);
      setSuccess("Perfil do Hermes Cliente atualizado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar perfil");
    } finally {
      setSaving(false);
    }
  }

  async function handleActivateSuggestion(skillKey: string) {
    setError("");
    setSuccess("");
    try {
      await activateClientSkill(skillKey);
      await loadClientHermes();
      setSuccess(`Skill ${skillKey} ativada com confirmação.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao ativar skill");
    }
  }

  async function handleToggleSkill(skillId: number, ativa: boolean) {
    setError("");
    setSuccess("");
    try {
      await toggleClientSkill(skillId, ativa);
      await loadClientHermes();
      setSuccess(`Skill ${ativa ? "ativada" : "desativada"} com sucesso.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar skill");
    }
  }

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

      <form onSubmit={handleSaveProfile} className="rounded-[32px] bg-white p-6 shadow-soft xl:col-span-2">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-serif text-2xl">Hermes Cliente</h2>
            <p className="mt-2 text-sm text-slate-600">
              Perfil, aprendizado e automações controladas por confirmação explícita.
            </p>
          </div>
          <button
            type="button"
            onClick={loadClientHermes}
            className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200"
          >
            Atualizar
          </button>
        </div>

        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        {success ? <div className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{success}</div> : null}

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <input
            className="input"
            placeholder="Tipo de negócio"
            value={form.tipo_negocio}
            onChange={(e) => setForm((current) => ({ ...current, tipo_negocio: e.target.value }))}
          />
          <select
            className="input"
            value={form.nivel_automacao}
            onChange={(e) => setForm((current) => ({ ...current, nivel_automacao: e.target.value }))}
          >
            <option value="baixo">Baixo</option>
            <option value="medio">Médio</option>
            <option value="alto">Alto</option>
          </select>
          <textarea
            className="input min-h-24 md:col-span-2"
            placeholder="Objetivo do cliente"
            value={form.objetivo}
            onChange={(e) => setForm((current) => ({ ...current, objetivo: e.target.value }))}
          />
          <input
            className="input"
            placeholder="Horário de funcionamento"
            value={form.horario_funcionamento}
            onChange={(e) => setForm((current) => ({ ...current, horario_funcionamento: e.target.value }))}
          />
          <textarea
            className="input min-h-24"
            placeholder="Preferências do Hermes"
            value={form.preferencias}
            onChange={(e) => setForm((current) => ({ ...current, preferencias: e.target.value }))}
          />
        </div>

        <button
          disabled={saving || loading}
          className="mt-6 rounded-2xl bg-brand px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Salvando..." : "Salvar perfil do Hermes"}
        </button>

        <div className="mt-8 grid gap-6 xl:grid-cols-2">
          <div className="rounded-[28px] bg-panel p-5">
            <h3 className="font-serif text-xl text-ink">Sugestões do Hermes</h3>
            <div className="mt-4 space-y-3">
              {loading ? (
                <div className="text-sm text-slate-500">Carregando sugestões...</div>
              ) : clientSuggestions.length === 0 ? (
                <div className="text-sm text-slate-500">
                  Ainda não há sugestões registradas. Elas aparecem quando o Hermes identifica padrões do tenant.
                </div>
              ) : (
                clientSuggestions.map((item) => (
                  <div key={item.skill_key} className="rounded-2xl bg-white p-4">
                    <div className="font-semibold text-slate-900">{item.skill_key}</div>
                    <div className="mt-2 text-sm text-slate-600">{item.message}</div>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <div className="text-xs text-slate-500">
                        {item.suggested_at ? `Sugerido em ${formatDateTime(item.suggested_at)}` : "Sugestão registrada"}
                      </div>
                      <button
                        type="button"
                        disabled={item.active}
                        onClick={() => handleActivateSuggestion(item.skill_key)}
                        className="rounded-2xl bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {item.active ? "Já ativa" : "Confirmar e ativar"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-[28px] bg-panel p-5">
            <h3 className="font-serif text-xl text-ink">Skills do cliente</h3>
            <div className="mt-4 space-y-3">
              {loading ? (
                <div className="text-sm text-slate-500">Carregando skills...</div>
              ) : clientSkills.length === 0 ? (
                <div className="text-sm text-slate-500">Nenhuma skill registrada para este tenant.</div>
              ) : (
                clientSkills.map((skill) => (
                  <div key={skill.id} className="rounded-2xl bg-white p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold text-slate-900">{skill.nome_skill}</div>
                        <div className="mt-1 text-sm text-slate-600">{skill.descricao || "Skill do cliente"}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleToggleSkill(skill.id, !skill.ativa)}
                        className={`rounded-2xl px-4 py-2 text-sm font-semibold ${
                          skill.ativa ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {skill.ativa ? "Ativa" : "Desligada"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {clientProfile ? (
          <div className="mt-6 text-xs text-slate-500">
            Perfil Hermes atualizado em {formatDateTime(clientProfile.updated_at)}.
          </div>
        ) : null}
      </form>
    </div>
  );
}

// Old CrmWorkspace replaced by modular components (see crm/CrmWorkspace.tsx)
// Kept for reference only - now using CrmWorkspace.tsx with separate pages

function SocialAccountsList({
  accounts,
  onDisconnect,
}: {
  accounts: SocialIntegrationAccount[];
  onDisconnect?: (accountId: number) => Promise<void>;
}) {
  if (accounts.length === 0) {
    return <div className="text-sm text-slate-500">Nenhuma conta conectada.</div>;
  }

  return (
    <div className="space-y-3">
      {accounts.map((account) => (
        <div key={account.id} className="flex items-center justify-between rounded-2xl bg-panel p-4">
          <div>
            <div className="font-semibold text-slate-900">{account.display_name || account.username || account.provider}</div>
            <div className="text-sm text-slate-600">
              {account.provider} • {account.status}
            </div>
          </div>
          {onDisconnect ? (
            <button
              onClick={() => onDisconnect(account.id)}
              className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200"
            >
              Desconectar
            </button>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function InstagramPage({ profile }: { profile: MeResponse }) {
  const [accounts, setAccounts] = useState<SocialIntegrationAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAccounts() {
    setLoading(true);
    setError("");
    try {
      const response = await getIntegrationAccounts("instagram");
      setAccounts(response.accounts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar contas");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAccounts();
  }, []);

  async function handleConnect() {
    const clientId = window.prompt("Client ID do Instagram/Meta:");
    const redirectUri = window.prompt("Redirect URI do Instagram:");
    if (!clientId || !redirectUri) return;
    try {
      const response = await startInstagramConnect({
        tenant_id: profile.tenant.id,
        user_id: profile.user.id,
        client_id: clientId,
        redirect_uri: redirectUri,
      });
      window.open(response.oauth_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao iniciar OAuth");
    }
  }

  async function handleDisconnect(accountId: number) {
    try {
      await disconnectIntegrationAccount(accountId);
      await loadAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desconectar conta");
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Instagram</h2>
        <p className="mt-3 text-slate-600">Gerencie contas conectadas e prepare a publicação integrada ao CRM.</p>
        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        <div className="mt-6 flex gap-3">
          <button onClick={handleConnect} className="rounded-2xl bg-gradient-to-r from-fuchsia-500 to-rose-500 px-6 py-3 text-sm font-semibold text-white">
            Conectar Instagram
          </button>
          <button onClick={loadAccounts} className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
            Atualizar
          </button>
        </div>
        <div className="mt-6">
          {loading ? <div className="text-sm text-slate-500">Carregando contas...</div> : <SocialAccountsList accounts={accounts} onDisconnect={handleDisconnect} />}
        </div>
      </div>
    </div>
  );
}

function YouTubePage({ profile }: { profile: MeResponse }) {
  const [accounts, setAccounts] = useState<SocialIntegrationAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAccounts() {
    setLoading(true);
    setError("");
    try {
      const response = await getIntegrationAccounts("youtube");
      setAccounts(response.accounts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar canais");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAccounts();
  }, []);

  async function handleConnect() {
    const clientId = window.prompt("Client ID do YouTube/Google:");
    const redirectUri = window.prompt("Redirect URI do YouTube:");
    if (!clientId || !redirectUri) return;
    try {
      const response = await startYouTubeConnect({
        tenant_id: profile.tenant.id,
        user_id: profile.user.id,
        client_id: clientId,
        redirect_uri: redirectUri,
      });
      window.open(response.oauth_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao iniciar OAuth");
    }
  }

  async function handleDisconnect(accountId: number) {
    try {
      await disconnectIntegrationAccount(accountId);
      await loadAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desconectar canal");
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">YouTube</h2>
        <p className="mt-3 text-slate-600">Gerencie canais conectados e use o publicador para vídeos e Shorts.</p>
        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        <div className="mt-6 flex gap-3">
          <button onClick={handleConnect} className="rounded-2xl bg-gradient-to-r from-red-500 to-red-600 px-6 py-3 text-sm font-semibold text-white">
            Conectar YouTube
          </button>
          <button onClick={loadAccounts} className="rounded-2xl bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
            Atualizar
          </button>
        </div>
        <div className="mt-6">
          {loading ? <div className="text-sm text-slate-500">Carregando canais...</div> : <SocialAccountsList accounts={accounts} onDisconnect={handleDisconnect} />}
        </div>
      </div>
    </div>
  );
}

function ContentPublisherPage() {
  const [stats, setStats] = useState<SocialIntegrationStats | null>(null);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "",
    content: "",
    media_type: "image",
    media_url: "",
    thumbnail_url: "",
    hashtags: "",
    caption: "",
    scheduled_at: "",
    instagram: true,
    youtube: false,
  });

  async function loadPublisher() {
    setLoading(true);
    setError("");
    try {
      const [statsResponse, postsResponse] = await Promise.all([getIntegrationStats(), getIntegrationPosts()]);
      setStats(statsResponse);
      setPosts(postsResponse.posts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar publicador");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPublisher();
  }, []);

  async function handleCreatePost(event: FormEvent) {
    event.preventDefault();
    const platforms = [form.instagram ? "instagram" : null, form.youtube ? "youtube" : null].filter(Boolean) as string[];
    if (!platforms.length) {
      setError("Selecione pelo menos uma plataforma");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createIntegrationPost({
        title: form.title,
        content: form.content,
        media_type: form.media_type,
        media_url: form.media_url,
        thumbnail_url: form.thumbnail_url || null,
        hashtags: form.hashtags || null,
        caption: form.caption || null,
        platforms,
        scheduled_at: form.scheduled_at || null,
      });
      setForm({
        title: "",
        content: "",
        media_type: "image",
        media_url: "",
        thumbnail_url: "",
        hashtags: "",
        caption: "",
        scheduled_at: "",
        instagram: true,
        youtube: false,
      });
      await loadPublisher();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar publicação");
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish(postId: number) {
    try {
      await publishIntegrationPost(postId);
      await loadPublisher();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao publicar conteúdo");
    }
  }

  async function handleDelete(postId: number) {
    try {
      await deleteIntegrationPost(postId);
      await loadPublisher();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir publicação");
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-[28px] bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Contas ativas</div>
          <div className="mt-2 text-3xl font-semibold text-ink">{stats?.accounts.active ?? "-"}</div>
        </div>
        <div className="rounded-[28px] bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Posts totais</div>
          <div className="mt-2 text-3xl font-semibold text-ink">{stats?.posts.total ?? "-"}</div>
        </div>
        <div className="rounded-[28px] bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Agendados</div>
          <div className="mt-2 text-3xl font-semibold text-ink">{stats?.posts.scheduled ?? "-"}</div>
        </div>
        <div className="rounded-[28px] bg-white p-5 shadow-soft">
          <div className="text-sm text-slate-500">Publicados</div>
          <div className="mt-2 text-3xl font-semibold text-ink">{stats?.posts.published ?? "-"}</div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
        <form onSubmit={handleCreatePost} className="rounded-[32px] bg-white p-6 shadow-soft">
          <h2 className="font-serif text-2xl">Nova publicação</h2>
          {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
          <div className="mt-5 grid gap-4">
            <input className="input" placeholder="Título" value={form.title} onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))} required />
            <textarea className="input min-h-28" placeholder="Conteúdo" value={form.content} onChange={(e) => setForm((current) => ({ ...current, content: e.target.value }))} required />
            <input className="input" placeholder="URL da mídia" value={form.media_url} onChange={(e) => setForm((current) => ({ ...current, media_url: e.target.value }))} required />
            <div className="grid gap-4 md:grid-cols-2">
              <select className="input" value={form.media_type} onChange={(e) => setForm((current) => ({ ...current, media_type: e.target.value }))}>
                <option value="image">Imagem</option>
                <option value="video">Vídeo</option>
                <option value="reel">Reel</option>
                <option value="short">Short</option>
              </select>
              <input className="input" type="datetime-local" value={form.scheduled_at} onChange={(e) => setForm((current) => ({ ...current, scheduled_at: e.target.value }))} />
            </div>
            <input className="input" placeholder="Thumbnail URL (opcional)" value={form.thumbnail_url} onChange={(e) => setForm((current) => ({ ...current, thumbnail_url: e.target.value }))} />
            <input className="input" placeholder="Legenda (opcional)" value={form.caption} onChange={(e) => setForm((current) => ({ ...current, caption: e.target.value }))} />
            <input className="input" placeholder="Hashtags (opcional)" value={form.hashtags} onChange={(e) => setForm((current) => ({ ...current, hashtags: e.target.value }))} />
            <div className="flex gap-6 text-sm text-slate-700">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={form.instagram} onChange={(e) => setForm((current) => ({ ...current, instagram: e.target.checked }))} />
                Instagram
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={form.youtube} onChange={(e) => setForm((current) => ({ ...current, youtube: e.target.checked }))} />
                YouTube
              </label>
            </div>
          </div>
          <button disabled={saving} className="mt-6 rounded-2xl bg-brand px-5 py-3 font-medium text-white disabled:opacity-50">
            {saving ? "Salvando..." : "Salvar publicação"}
          </button>
        </form>

        <div className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-2xl">Fila de publicações</h2>
            <button onClick={loadPublisher} className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200">
              Atualizar
            </button>
          </div>
          <div className="mt-5 space-y-3">
            {loading ? (
              <div className="text-sm text-slate-500">Carregando publicações...</div>
            ) : posts.length === 0 ? (
              <div className="text-sm text-slate-500">Nenhuma publicação cadastrada.</div>
            ) : (
              posts.map((post) => (
                <div key={post.id} className="rounded-2xl bg-panel p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-semibold text-slate-900">{post.title}</div>
                       <div className="mt-1 text-sm text-slate-600">{post.platforms.join(", ")} • {post.status}</div>
                      <div className="mt-2 text-sm text-slate-500">{post.media_url}</div>
                    </div>
                    <div className="flex gap-2">
                      {post.status !== "published" ? (
                        <button onClick={() => handlePublish(post.id)} className="rounded-2xl bg-brand px-4 py-2 text-sm font-semibold text-white">
                          Publicar
                        </button>
                      ) : null}
                      <button onClick={() => handleDelete(post.id)} className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200">
                        Excluir
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── helpers para Agenda ───────────────────────────────────────────────────────

type AgendaItem =
  | { kind: "reminder"; date: Date; data: AgentReminder }
  | { kind: "appointment"; date: Date; data: AgentAppointment }
  | { kind: "followup"; date: Date; data: CrmFollowup }
  | { kind: "task"; date: Date; data: CrmTask };

const AGENDA_KIND_META: Record<AgendaItem["kind"], { label: string; icon: string; color: string }> = {
  reminder:    { label: "Lembrete",    icon: "🔔", color: "bg-violet-50 border-violet-200" },
  appointment: { label: "Compromisso", icon: "📅", color: "bg-blue-50 border-blue-200" },
  followup:    { label: "Follow-up",   icon: "📞", color: "bg-amber-50 border-amber-200" },
  task:        { label: "Tarefa",      icon: "✅", color: "bg-emerald-50 border-emerald-200" },
};

function agendaItemDate(item: AgendaItem): string {
  if (item.kind === "reminder")    return item.data.remind_at;
  if (item.kind === "appointment") return item.data.scheduled_at;
  if (item.kind === "followup")    return item.data.due_at || item.data.data_hora || "";
  return item.data.due_at || "";
}

function agendaItemTitle(item: AgendaItem): string {
  if (item.kind === "followup") return item.data.title || item.data.titulo || "";
  return item.data.title;
}

function agendaItemStatus(item: AgendaItem): string {
  return item.data.status;
}

function agendaItemDesc(item: AgendaItem): string | null | undefined {
  if (item.kind === "task") return item.data.description;
  if (item.kind === "appointment") return item.data.location ? `📍 ${item.data.location}` : item.data.description;
  return (item.data as AgentReminder | CrmFollowup).description;
}

function isAgendaItemDone(item: AgendaItem): boolean {
  const s = agendaItemStatus(item);
  return ["done", "feito", "completed", "sent", "cancelled", "concluido"].includes(s);
}

function relativeDay(date: Date): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diff = Math.round((target.getTime() - today.getTime()) / 86400000);
  if (diff === 0) return "Hoje";
  if (diff === 1) return "Amanhã";
  if (diff === -1) return "Ontem";
  if (diff < 0) return `${Math.abs(diff)} dias atrás`;
  return `em ${diff} dias`;
}

function AgendaPage() {
  const [reminders, setReminders]       = useState<AgentReminder[]>([]);
  const [appointments, setAppointments] = useState<AgentAppointment[]>([]);
  const [followups, setFollowups]       = useState<CrmFollowup[]>([]);
  const [tasks, setTasks]               = useState<CrmTask[]>([]);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState("");
  const [showDone, setShowDone]         = useState(false);
  const [updating, setUpdating]         = useState<string | null>(null);

  async function loadAgenda() {
    setLoading(true);
    setError("");
    try {
      const [r, a, f, t] = await Promise.allSettled([
        getAgendaReminders(true),
        getAgendaAppointments(true),
        getCrmFollowups(),
        getCrmTasks(),
      ]);
      if (r.status === "fulfilled") setReminders(r.value);
      if (a.status === "fulfilled") setAppointments(a.value);
      if (f.status === "fulfilled") setFollowups(f.value);
      if (t.status === "fulfilled") setTasks(t.value);
      if ([r, a, f, t].every((x) => x.status === "rejected")) {
        setError("Falha ao carregar agenda");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAgenda(); }, []);

  const allItems: AgendaItem[] = [
    ...reminders.map((d): AgendaItem => ({ kind: "reminder", date: new Date(d.remind_at), data: d })),
    ...appointments.map((d): AgendaItem => ({ kind: "appointment", date: new Date(d.scheduled_at), data: d })),
    ...followups.map((d): AgendaItem => ({ kind: "followup", date: new Date(d.due_at || d.data_hora || Date.now()), data: d })),
    ...tasks.filter((t) => t.due_at).map((d): AgendaItem => ({ kind: "task", date: new Date(d.due_at!), data: d })),
  ].sort((a, b) => a.date.getTime() - b.date.getTime());

  const visibleItems = showDone ? allItems : allItems.filter((i) => !isAgendaItemDone(i));
  const pendingTasks = tasks.filter((t) => !t.due_at && !["feito", "completed", "done"].includes(t.status));

  async function markReminderDone(id: number) {
    const key = `reminder-${id}`;
    setUpdating(key);
    try {
      await updateAgendaReminder(id, "done");
      setReminders((prev) => prev.map((r) => (r.id === id ? { ...r, status: "done" } : r)));
    } finally {
      setUpdating(null);
    }
  }

  async function markAppointmentDone(id: number) {
    const key = `appointment-${id}`;
    setUpdating(key);
    try {
      await updateAgendaAppointment(id, "done");
      setAppointments((prev) => prev.map((a) => (a.id === id ? { ...a, status: "done" } : a)));
    } finally {
      setUpdating(null);
    }
  }

  function renderDoneButton(item: AgendaItem) {
    if (isAgendaItemDone(item)) return null;
    if (item.kind === "reminder") {
      const key = `reminder-${item.data.id}`;
      return (
        <button
          disabled={updating === key}
          onClick={() => markReminderDone(item.data.id)}
          className="ml-2 shrink-0 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 shadow-sm hover:bg-emerald-50 hover:text-emerald-700 disabled:opacity-40"
        >
          {updating === key ? "…" : "Concluir"}
        </button>
      );
    }
    if (item.kind === "appointment") {
      const key = `appointment-${item.data.id}`;
      return (
        <button
          disabled={updating === key}
          onClick={() => markAppointmentDone(item.data.id)}
          className="ml-2 shrink-0 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 shadow-sm hover:bg-emerald-50 hover:text-emerald-700 disabled:opacity-40"
        >
          {updating === key ? "…" : "Concluir"}
        </button>
      );
    }
    return null;
  }

  const stats = {
    total: allItems.length,
    overdue: allItems.filter((i) => !isAgendaItemDone(i) && i.date < new Date()).length,
    today: allItems.filter((i) => relativeDay(i.date) === "Hoje").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-serif text-3xl text-ink">Agenda</h1>
            <p className="mt-1 text-sm text-slate-500">
              Lembretes, compromissos, follow-ups e tarefas — tudo em um lugar
            </p>
          </div>
          <button
            onClick={loadAgenda}
            disabled={loading}
            className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200 disabled:opacity-50"
          >
            {loading ? "Carregando…" : "↻ Atualizar"}
          </button>
        </div>

        {/* Stats bar */}
        <div className="mt-5 flex flex-wrap gap-4">
          {[
            { label: "Total pendente", value: stats.total - allItems.filter(isAgendaItemDone).length, color: "text-slate-700" },
            { label: "Hoje",           value: stats.today,   color: "text-violet-600" },
            { label: "Atrasados",      value: stats.overdue, color: stats.overdue > 0 ? "text-red-600" : "text-slate-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-2xl bg-panel px-4 py-2 text-center">
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
              <div className="text-xs text-slate-500">{label}</div>
            </div>
          ))}
          <label className="ml-auto flex cursor-pointer items-center gap-2 text-sm text-slate-500">
            <input
              type="checkbox"
              checked={showDone}
              onChange={(e) => setShowDone(e.target.checked)}
              className="h-4 w-4 accent-violet-600"
            />
            Mostrar concluídos
          </label>
        </div>

        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
      </div>

      {/* Timeline */}
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-xl text-ink">Linha do tempo</h2>
        <div className="mt-5 space-y-3">
          {loading ? (
            <div className="py-10 text-center text-sm text-slate-400">Carregando agenda…</div>
          ) : visibleItems.length === 0 ? (
            <div className="py-10 text-center text-sm text-slate-400">
              {showDone ? "Nenhum item na agenda." : "Nenhum item pendente. 🎉"}
            </div>
          ) : (
            visibleItems.map((item) => {
              const meta = AGENDA_KIND_META[item.kind];
              const done = isAgendaItemDone(item);
              const overdue = !done && item.date < new Date();
              const dateStr = agendaItemDate(item);
              const desc = agendaItemDesc(item);

              return (
                <div
                  key={`${item.kind}-${item.data.id}`}
                  className={`flex items-start gap-3 rounded-2xl border p-4 transition ${
                    done ? "opacity-50" : overdue ? "border-red-200 bg-red-50" : meta.color
                  }`}
                >
                  <span className="mt-0.5 text-lg">{meta.icon}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`text-sm font-semibold ${done ? "line-through text-slate-400" : "text-slate-900"}`}>
                        {agendaItemTitle(item)}
                      </span>
                      <span className="rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                        {meta.label}
                      </span>
                      {overdue && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-600">
                          Atrasado
                        </span>
                      )}
                    </div>
                    {desc ? <div className="mt-0.5 truncate text-xs text-slate-500">{desc}</div> : null}
                    <div className="mt-1 text-xs text-slate-400">
                      {dateStr ? (
                        <>
                          {new Date(dateStr).toLocaleString("pt-BR", {
                            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                          })}
                          {" · "}
                          <span className={overdue ? "font-semibold text-red-500" : "text-slate-500"}>
                            {relativeDay(item.date)}
                          </span>
                        </>
                      ) : "Sem data"}
                    </div>
                  </div>
                  {renderDoneButton(item)}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Tarefas sem data */}
      {pendingTasks.length > 0 && (
        <div className="rounded-[32px] bg-white p-6 shadow-soft">
          <h2 className="font-serif text-xl text-ink">Tarefas sem data</h2>
          <div className="mt-5 space-y-2">
            {pendingTasks.map((task) => (
              <div key={task.id} className="flex items-center gap-3 rounded-2xl bg-panel px-4 py-3">
                <span className="text-lg">✅</span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold text-slate-800">{task.title}</div>
                  {task.description && (
                    <div className="mt-0.5 truncate text-xs text-slate-400">{task.description}</div>
                  )}
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                  task.priority === "alta" ? "bg-red-100 text-red-600" :
                  task.priority === "media" ? "bg-amber-100 text-amber-600" :
                  "bg-slate-100 text-slate-500"
                }`}>
                  {task.priority || "normal"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ModuleRoute({
  enabled,
  children,
  fallback = "/dashboard",
}: {
  enabled: boolean;
  children: React.ReactNode;
  fallback?: string;
}) {
  if (!enabled) {
    return <Navigate to={fallback} replace />;
  }
  return <>{children}</>;
}

function HermesAdminChatPage({ profile }: { profile: MeResponse }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState<HermesAdminDashboard | null>(null);
  const quickCommands = [
    "status do sistema",
    "listar módulos",
    "ver erros",
    "analisar projeto",
    "o que falta fazer",
  ];
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
      const message = err instanceof Error ? err.message : "Falha ao falar com Hermes Admin";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant-error`,
          sender: "assistant",
          content: `Não consegui concluir a chamada do assistente agora.\n${message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleQuickCommand(command: string) {
    if (loading) return;
    setContent(command);
  }

  return (
    <div className="grid min-h-[calc(100vh-3rem)] gap-4 xl:grid-cols-[320px,1fr]">
      <section className="rounded-[32px] bg-white p-5 shadow-soft sm:p-6">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Super Admin</div>
        <h2 className="mt-2 font-serif text-2xl sm:text-3xl">Hermes Admin</h2>
        <p className="mt-3 text-sm text-slate-600">
          Chat operacional global do SaaS para {profile.user.name}.
        </p>

        <div className="mt-6 grid gap-3 text-sm sm:grid-cols-3 xl:grid-cols-1">
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
          <div className="mt-3 flex flex-wrap gap-2">
            {quickCommands.map((command) => (
              <button
                key={command}
                type="button"
                onClick={() => handleQuickCommand(command)}
                className="rounded-full bg-white/10 px-3 py-2 text-left text-xs text-white transition hover:bg-white/20"
              >
                {command}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="flex flex-col overflow-hidden rounded-[32px] bg-[#efeae2] shadow-soft">
        <div className="border-b border-black/5 bg-white/90 px-4 py-4 backdrop-blur sm:px-6">
          <div className="font-medium">Hermes Super Admin</div>
          <div className="text-sm text-slate-500">Acesso global ao sistema</div>
        </div>

        <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_right,rgba(27,127,107,0.10),transparent_25%),linear-gradient(180deg,#efeae2,#e7dfd3)] p-4 sm:p-6">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`w-fit max-w-[88%] whitespace-pre-wrap rounded-[22px] px-4 py-3 text-sm shadow sm:max-w-[80%] ${
                  message.sender === "user" ? "ml-auto bg-bubble" : "bg-white"
                }`}
              >
                {message.content}
              </div>
            ))}
            {loading ? <div className="w-fit max-w-[88%] rounded-[22px] bg-white px-4 py-3 text-sm text-slate-500 shadow sm:max-w-[80%]">Hermes está processando...</div> : null}
            {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="border-t border-black/5 bg-white/90 p-4 backdrop-blur">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              className="input flex-1"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Pergunte sobre status, módulos, erros ou projeto"
            />
            <button
              disabled={loading}
              className="rounded-2xl bg-brand px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 sm:min-w-[140px]"
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
  const [connection, setConnection] = useState<CrmWhatsAppConnection | null>(null);
  const [statusInfo, setStatusInfo] = useState<CrmWhatsAppStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    provider: "evolution_go",
    instance_name: "",
    api_base_url: "",
    api_key: "",
    webhook_url: "",
  });

  async function loadWhatsApp() {
    setLoading(true);
    setError("");
    try {
      const [connectionData, statusData] = await Promise.all([
        getCrmWhatsAppConnection(),
        getCrmWhatsAppStatus().catch(() => null),
      ]);
      setConnection(connectionData);
      setStatusInfo(statusData);
      if (connectionData) {
        setForm({
          provider: connectionData.provider,
          instance_name: connectionData.instance_name,
          api_base_url: connectionData.api_base_url || "",
          api_key: "",
          webhook_url: connectionData.webhook_url || "",
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar WhatsApp");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWhatsApp();
  }, []);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await upsertCrmWhatsAppConnection({
        provider: form.provider,
        instance_name: form.instance_name,
        api_base_url: form.api_base_url || null,
        api_key: form.api_key || null,
        webhook_url: form.webhook_url || null,
      });
      await loadWhatsApp();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar conexão");
    } finally {
      setSaving(false);
    }
  }

  async function handleConnect() {
    setError("");
    try {
      await connectCrmWhatsApp();
      const qr = await getCrmWhatsAppQrCode().catch(() => null);
      setStatusInfo(qr || (await getCrmWhatsAppStatus()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao conectar WhatsApp");
    }
  }

  async function handleDisconnect() {
    setError("");
    try {
      await disconnectCrmWhatsApp();
      await loadWhatsApp();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desconectar WhatsApp");
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr,0.95fr]">
      <form onSubmit={handleSave} className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">WhatsApp CRM</h2>
        <p className="mt-3 text-slate-600">Configure a instância do provedor e gerencie o QR Code da conexão.</p>
        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        <div className="mt-5 grid gap-4">
          <input className="input" placeholder="Provider" value={form.provider} onChange={(e) => setForm((current) => ({ ...current, provider: e.target.value }))} required />
          <input className="input" placeholder="Nome da instância" value={form.instance_name} onChange={(e) => setForm((current) => ({ ...current, instance_name: e.target.value }))} required />
          <input className="input" placeholder="API Base URL" value={form.api_base_url} onChange={(e) => setForm((current) => ({ ...current, api_base_url: e.target.value }))} />
          <input className="input" placeholder="API Key" value={form.api_key} onChange={(e) => setForm((current) => ({ ...current, api_key: e.target.value }))} />
          <input className="input" placeholder="Webhook URL" value={form.webhook_url} onChange={(e) => setForm((current) => ({ ...current, webhook_url: e.target.value }))} />
        </div>
        <button disabled={saving} className="mt-6 rounded-2xl bg-brand px-5 py-3 font-medium text-white disabled:opacity-50">
          {saving ? "Salvando..." : "Salvar conexão"}
        </button>
      </form>

      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Estado da conexão</h2>
        {loading ? <div className="mt-5 text-sm text-slate-500">Carregando status...</div> : null}
        <div className="mt-5 space-y-4">
          <div className="rounded-2xl bg-panel p-4">
            <div className="text-sm text-slate-500">Status</div>
            <div className="mt-1 text-lg font-semibold text-ink">{statusInfo?.status || connection?.status || "disconnected"}</div>
          </div>
          <div className="rounded-2xl bg-panel p-4">
            <div className="text-sm text-slate-500">Telefone conectado</div>
            <div className="mt-1 text-lg font-semibold text-ink">{statusInfo?.connected_phone || connection?.connected_phone || "-"}</div>
          </div>
          {statusInfo?.qr_code_base64 ? (
            <div className="rounded-2xl bg-panel p-4">
              <div className="text-sm text-slate-500">QR Code</div>
              <img
                className="mt-3 max-w-xs rounded-2xl bg-white p-3"
                src={`data:image/png;base64,${statusInfo.qr_code_base64}`}
                alt="QR Code WhatsApp"
              />
            </div>
          ) : null}
          <div className="flex gap-3">
            <button onClick={handleConnect} type="button" className="rounded-2xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white">
              Conectar
            </button>
            <button onClick={loadWhatsApp} type="button" className="rounded-2xl bg-slate-100 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
              Atualizar
            </button>
            <button onClick={handleDisconnect} type="button" className="rounded-2xl bg-slate-100 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200">
              Desconectar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MasterPage({
  profile,
  onProfileRefresh,
}: {
  profile: MeResponse;
  onProfileRefresh: () => Promise<void>;
}) {
  const [tenants, setTenants] = useState<AdminTenant[]>([]);
  const [savingTenantId, setSavingTenantId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const moduleDefs = [
    { key: "crm", label: "CRM", enabledKey: "crm_enabled" as const },
    { key: "whatsapp_evolution", label: "WhatsApp", enabledKey: "whatsapp_evolution_enabled" as const },
    { key: "kanban", label: "Kanban", enabledKey: "kanban_enabled" as const },
    { key: "agenda", label: "Agenda", enabledKey: "agenda_enabled" as const },
    { key: "instagram", label: "Instagram", enabledKey: "instagram_enabled" as const },
    { key: "youtube", label: "YouTube", enabledKey: "youtube_enabled" as const },
    { key: "content_publisher", label: "Content Publisher", enabledKey: "content_publisher_enabled" as const },
    { key: "agenda_pastoral", label: "Agenda Pastoral", enabledKey: "agenda_pastoral_enabled" as const },
  ] as const;

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

  async function toggleModule(tenant: AdminTenant, moduleKey: (typeof moduleDefs)[number]["key"], enabled: boolean) {
    setSavingTenantId(tenant.id);
    setError("");
    try {
      const updated = await updateAdminTenantModules(tenant.id, { [moduleKey]: enabled });
      if (updated.id === profile.tenant.id) {
        await onProfileRefresh();
      }
      setTenants((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar tenant");
    } finally {
      setSavingTenantId(null);
    }
  }

  if (!profile.user.is_super_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-[linear-gradient(135deg,#2a1f43,#3d2d63_55%,#e6d7b7)] p-6 text-white shadow-soft sm:p-8">
        <div className="text-xs uppercase tracking-[0.3em] text-white/60">Admin Master</div>
        <h2 className="mt-3 font-serif text-3xl sm:text-4xl">Módulos por cliente</h2>
        <p className="mt-3 max-w-2xl text-sm text-white/75">
          Controle central para ativar ou desativar módulos por tenant sem misturar dados entre clientes.
        </p>
      </div>

      {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}

      <div className="rounded-[32px] bg-white p-4 shadow-soft sm:p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <h3 className="font-serif text-2xl">Tenants</h3>
          <div className="text-sm text-slate-500">{tenants.length} clientes</div>
        </div>

        <div className="mt-5 space-y-4 lg:hidden">
          {tenants.map((tenant) => (
            <div key={tenant.id} className="rounded-[28px] border border-black/5 bg-slate-50 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate font-semibold text-ink">{tenant.name}</div>
                  <div className="truncate text-sm text-slate-500">{tenant.email}</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">{tenant.plan}</div>
                </div>
                <span className={`shrink-0 rounded-full px-3 py-1 text-xs ${tenant.active ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
                  {tenant.active ? "ativo" : "inativo"}
                </span>
              </div>

              <div className="mt-4 grid gap-3">
                {moduleDefs.map((moduleDef) => (
                  <label key={moduleDef.key} className="flex items-center justify-between gap-3 rounded-2xl bg-white px-4 py-3">
                    <span className="text-sm font-medium text-slate-700">{moduleDef.label}</span>
                    <input
                      type="checkbox"
                      checked={tenant[moduleDef.enabledKey]}
                      disabled={savingTenantId === tenant.id}
                      onChange={(event) => void toggleModule(tenant, moduleDef.key, event.target.checked)}
                    />
                  </label>
                ))}
              </div>

              <div className="mt-4 text-xs text-slate-400">Criado em {formatDateTime(tenant.created_at)}</div>
            </div>
          ))}
        </div>

        <div className="mt-5 hidden overflow-x-auto lg:block">
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
                        onChange={(event) => void toggleModule(tenant, "crm", event.target.checked)}
                      />
                      <span className="text-slate-700">{tenant.crm_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.whatsapp_evolution_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={(event) => void toggleModule(tenant, "whatsapp_evolution", event.target.checked)}
                      />
                      <span className="text-slate-700">{tenant.whatsapp_evolution_enabled ? "habilitado" : "desligado"}</span>
                    </label>
                  </td>
                  <td className="px-3 py-4">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={tenant.kanban_enabled}
                        disabled={savingTenantId === tenant.id}
                        onChange={(event) => void toggleModule(tenant, "kanban", event.target.checked)}
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
                        onChange={(event) => void toggleModule(tenant, "agenda", event.target.checked)}
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
                        onChange={(event) => void toggleModule(tenant, "instagram", event.target.checked)}
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
                        onChange={(event) => void toggleModule(tenant, "youtube", event.target.checked)}
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
                        onChange={(event) => void toggleModule(tenant, "content_publisher", event.target.checked)}
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
  const [clientProfile, setClientProfile] = useState<ClientProfile | null>(null);
  const [clientSkills, setClientSkills] = useState<ClientSkill[]>([]);
  const [clientSuggestions, setClientSuggestions] = useState<ClientSuggestion[]>([]);

  async function loadProfileWithModules() {
    const profileData = await me();
    const modulesData = await getTenantModules().catch(() => profileData.modules);
    return {
      ...profileData,
      modules: {
        ...profileData.modules,
        ...modulesData,
      },
    };
  }

  useEffect(() => {
    loadProfileWithModules()
      .then(async (profileData) => {
        const [chatsData, creditsData, leadsData, tasksData, clientProfileData, clientSkillsData, clientSuggestionsData] = await Promise.all([
          getChats(),
          getCredits(),
          profileData.modules.crm ? getLeads() : Promise.resolve([]),
          profileData.modules.crm ? getTasks() : Promise.resolve([]),
          getClientProfile().catch(() => null),
          getClientSkills().catch(() => []),
          getClientSuggestions().catch(() => []),
        ]);
        setProfile(profileData);
        setChats(chatsData);
        setLeads(leadsData);
        setTasks(tasksData);
        setCredits(creditsData);
        setClientProfile(clientProfileData);
        setClientSkills(clientSkillsData);
        setClientSuggestions(clientSuggestionsData);
        if (chatsData.length > 0) {
          setSelectedChatId(chatsData[0].id);
        }
      })
      .catch(() => {
        localStorage.removeItem("hermes_token");
        window.location.href = "/";
      });
  }, []);

  async function refreshProfile() {
    const profileData = await loadProfileWithModules();
    setProfile(profileData);
  }

  async function refreshClientHermes() {
    const [profileData, skillsData, suggestionsData] = await Promise.all([
      getClientProfile().catch(() => null),
      getClientSkills().catch(() => []),
      getClientSuggestions().catch(() => []),
    ]);
    setClientProfile(profileData);
    setClientSkills(skillsData);
    setClientSuggestions(suggestionsData);
  }

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
        <Route
          path="/dashboard"
          element={
            <DashboardPage
              chats={chats}
              credits={credits}
              leads={leads}
              tasks={tasks}
              clientProfile={clientProfile}
              clientSkills={clientSkills}
              clientSuggestions={clientSuggestions}
            />
          }
        />
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
                clientProfile={clientProfile}
                clientSuggestions={clientSuggestions}
                clientSkills={clientSkills}
                onSelectChat={(chat) => setSelectedChatId(chat.id)}
                onSendMessage={async (content) => {
                  if (!selectedChat) return;
                  await sendMessage(selectedChat.id, content);
                  const [items, nextTasks] = await Promise.all([
                    getMessages(selectedChat.id),
                    profile.modules.crm ? getTasks() : Promise.resolve(tasks),
                  ]);
                  setMessages(items);
                  setTasks(nextTasks);
                  await refreshClientHermes();
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
          <Route
            path="/crm/*"
            element={
              <ModuleRoute enabled={profile.modules.crm}>
                <CrmWorkspace profile={profile} />
            </ModuleRoute>
          }
        />
        <Route
          path="/crm/whatsapp"
          element={
            <ModuleRoute enabled={profile.modules.whatsapp_evolution}>
              <CrmWhatsAppPage />
            </ModuleRoute>
          }
        />
        <Route
          path="/crm/kanban"
          element={
            <ModuleRoute enabled={profile.modules.crm && profile.modules.kanban}>
              <CrmKanbanPage />
            </ModuleRoute>
          }
        />
        <Route
          path="/agenda"
          element={
            <ModuleRoute enabled={profile.modules.crm && profile.modules.agenda}>
              <AgendaPage />
            </ModuleRoute>
          }
        />
        <Route
          path="/instagram"
          element={
            <ModuleRoute enabled={profile.modules.instagram}>
              <InstagramPage profile={profile} />
            </ModuleRoute>
          }
        />
        <Route
          path="/youtube"
          element={
            <ModuleRoute enabled={profile.modules.youtube}>
              <YouTubePage profile={profile} />
            </ModuleRoute>
          }
        />
        <Route
          path="/publisher"
          element={
            <ModuleRoute enabled={profile.modules.content_publisher}>
              <ContentPublisherPage />
            </ModuleRoute>
          }
        />
        <Route
          path="/pastoral"
          element={
            <ModuleRoute enabled={profile.modules.agenda_pastoral}>
              <PastoralWorkspace />
            </ModuleRoute>
          }
        />
        <Route path="/master" element={<MasterPage profile={profile} onProfileRefresh={refreshProfile} />} />
        <Route
          path="/leads"
          element={
            <ModuleRoute enabled={profile.modules.crm}>
              <TablePage title="Leads" rows={leads} render={(row) => [row.name, row.phone || "-", row.interest || "-", row.status]} />
            </ModuleRoute>
          }
        />
        <Route
          path="/tasks"
          element={
            <ModuleRoute enabled={profile.modules.crm}>
              <TablePage title="Tarefas" rows={tasks} render={(row) => [row.title, row.description || "-", row.status, row.due_date || "-"]} />
            </ModuleRoute>
          }
        />
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
