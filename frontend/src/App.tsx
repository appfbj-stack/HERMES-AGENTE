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
  CrmTask,
  CrmWhatsAppConnection,
  CrmWhatsAppStatus,
  Lead,
  MeResponse,
  Message,
  Task,
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
    ...(profile.modules.crm ? [{ label: "CRM", path: "/crm" }] : []),
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
  const [tenantEmail, setTenantEmail] = useState("contato@empresa.com");
  const [email, setEmail] = useState("admin@empresa.com");
  const [password, setPassword] = useState("123456");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    try {
      const result = await login(email, password, tenantEmail.trim() || undefined);
      localStorage.setItem("hermes_token", result.access_token);
      onLogged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(140deg,#1b7f6b,#163b32_55%,#f1e9dc)] p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-[32px] bg-white p-8 shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Telegram + Hermes</div>
        <h1 className="mt-3 font-serif text-4xl font-semibold text-ink">Entrar</h1>
        <p className="mt-3 text-sm text-slate-500">Painel estilo chat com CRM, atendimento e operação multi-tenant.</p>
        <div className="mt-8 space-y-4">
          <input
            className="input"
            value={tenantEmail}
            onChange={(e) => setTenantEmail(e.target.value)}
            placeholder="Email da empresa / tenant"
          />
          <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Senha"
            type="password"
          />
        </div>
        {error ? <div className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}
        <button className="mt-6 w-full rounded-2xl bg-brand px-4 py-3 font-medium text-white">Acessar painel</button>
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

function CrmWorkspace({ profile }: { profile: MeResponse }) {
  const [dashboard, setDashboard] = useState<CrmDashboard | null>(null);
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [kanban, setKanban] = useState<CrmKanbanBoard | null>(null);
  const [conversations, setConversations] = useState<CrmConversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [crmMessages, setCrmMessages] = useState<CrmMessage[]>([]);
  const [followups, setFollowups] = useState<CrmFollowup[]>([]);
  const [crmTasks, setCrmTasks] = useState<CrmTask[]>([]);
  const [settings, setSettings] = useState<CrmSettings | null>(null);
  const [whatsAppConnection, setWhatsAppConnection] = useState<CrmWhatsAppConnection | null>(null);
  const [whatsAppStatus, setWhatsAppStatus] = useState<CrmWhatsAppStatus | null>(null);
  const [leadActivity, setLeadActivity] = useState<CrmActivityLog[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [messageDraft, setMessageDraft] = useState("");
  const [dragLeadId, setDragLeadId] = useState<number | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const [leadForm, setLeadForm] = useState({
    name: "",
    phone: "",
    email: "",
    origin: "manual",
    status: "Novo lead",
    notes: "",
  });
  const [editingLeadId, setEditingLeadId] = useState<number | null>(null);
  const [followupForm, setFollowupForm] = useState({
    title: "",
    description: "",
    due_at: "",
    channel: "whatsapp",
    status: "pendente",
  });
  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    due_at: "",
    priority: "media",
    status: "pendente",
  });
  const [editingFollowupId, setEditingFollowupId] = useState<number | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [settingsForm, setSettingsForm] = useState({
    initial_auto_message: "",
    status_options: "",
    tags: "",
    hermes_enabled: true,
  });
  const [whatsAppForm, setWhatsAppForm] = useState({
    provider: "evolution_go",
    instance_name: "",
    api_base_url: "",
    api_key: "",
    webhook_url: "",
  });
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");

  async function loadCrmData() {
    const [dashboardData, leadsData, kanbanData, conversationsData, followupsData, tasksData, settingsData, whatsAppConnectionData] =
      await Promise.all([
        getCrmDashboard(),
        getCrmLeads(),
        getCrmKanban(),
        getCrmConversations(),
        getCrmFollowups(true),
        getCrmTasks(),
        getCrmSettings(),
        getCrmWhatsAppConnection(),
      ]);

    setDashboard(dashboardData);
    setLeads(leadsData);
    setKanban(kanbanData);
    setConversations(conversationsData);
    setFollowups(followupsData);
    setCrmTasks(tasksData);
    setSettings(settingsData);
    setWhatsAppConnection(whatsAppConnectionData);
    setWhatsAppStatus(
      whatsAppConnectionData
        ? {
            status: whatsAppConnectionData.status,
            connected_phone: whatsAppConnectionData.connected_phone,
            qr_code_base64: whatsAppConnectionData.qr_code_base64,
            raw: null,
          }
        : null,
    );
    setSettingsForm({
      initial_auto_message: settingsData.initial_auto_message || "",
      status_options: settingsData.status_options.join(", "),
      tags: settingsData.tags.join(", "),
      hermes_enabled: settingsData.hermes_enabled,
    });
    setWhatsAppForm({
      provider: whatsAppConnectionData?.provider || "evolution_go",
      instance_name: whatsAppConnectionData?.instance_name || `tenant-${profile.tenant.id}-wa`,
      api_base_url: whatsAppConnectionData?.api_base_url || "",
      api_key: "",
      webhook_url: whatsAppConnectionData?.webhook_url || "",
    });

    if (!selectedConversationId && conversationsData.length > 0) {
      setSelectedConversationId(conversationsData[0].id);
    }
    if (!selectedLeadId) {
      const firstLeadId = leadsData[0]?.id ?? conversationsData[0]?.lead_id ?? null;
      setSelectedLeadId(firstLeadId);
    }
  }

  useEffect(() => {
    if (!profile.modules.crm) return;
    loadCrmData().catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar CRM"));
  }, [profile.modules.crm]);

  useEffect(() => {
    if (!profile.modules.crm || !selectedConversationId) return;
    getCrmMessages(selectedConversationId).then(setCrmMessages).catch(() => setCrmMessages([]));
  }, [profile.modules.crm, selectedConversationId]);

  useEffect(() => {
    if (!profile.modules.crm || !selectedLeadId) return;
    getCrmLeadActivity(selectedLeadId).then(setLeadActivity).catch(() => setLeadActivity([]));
  }, [profile.modules.crm, selectedLeadId]);

  if (!profile.modules.crm) {
    return (
      <div className="rounded-[32px] bg-white p-8 shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">CRM</div>
        <h2 className="mt-3 font-serif text-3xl">Módulo indisponível</h2>
        <p className="mt-4 max-w-2xl text-sm text-slate-600">
          O módulo CRM está desativado para este tenant. Ative `tenant_modules.crm = true` para liberar menu,
          backend e sincronização de conversas.
        </p>
      </div>
    );
  }

  const selectedConversation = conversations.find((conversation) => conversation.id === selectedConversationId);
  const selectedLead =
    leads.find((lead) => lead.id === selectedLeadId) ??
    (selectedConversation?.lead_id ? leads.find((lead) => lead.id === selectedConversation.lead_id) : undefined);

  const filteredLeads = leads.filter((lead) => {
    const term = filter.toLowerCase().trim();
    if (!term) return true;
    return [lead.name, lead.phone, lead.email, lead.status, lead.origin].some((value) =>
      (value || "").toLowerCase().includes(term),
    );
  });

  const summaryCards = dashboard
    ? [
        { label: "Leads", value: dashboard.total_leads },
        { label: "Novos", value: dashboard.new_leads },
        { label: "Conversas abertas", value: dashboard.open_conversations },
        { label: "Follow-ups hoje", value: dashboard.today_followups },
        { label: "Mensagens/mês", value: dashboard.messages_used_month },
        { label: "Plano", value: dashboard.current_plan },
      ]
    : [];
  const whatsAppQrCodeSrc = whatsAppStatus?.qr_code_base64
    ? whatsAppStatus.qr_code_base64.startsWith("data:")
      ? whatsAppStatus.qr_code_base64
      : `data:image/png;base64,${whatsAppStatus.qr_code_base64}`
    : null;

  async function refreshAfterMutation(options?: { keepLead?: boolean; keepConversation?: boolean }) {
    await loadCrmData();
    if (!options?.keepLead) {
      setSelectedLeadId((current) => current ?? leads[0]?.id ?? null);
    }
    if (!options?.keepConversation) {
      setSelectedConversationId((current) => current ?? conversations[0]?.id ?? null);
    }
  }

  async function handleCreateLead(event: FormEvent) {
    event.preventDefault();
    setSaving("lead");
    setError("");
    try {
      const lead = editingLeadId
        ? await updateCrmLead(editingLeadId, {
            name: leadForm.name,
            phone: leadForm.phone || undefined,
            email: leadForm.email || undefined,
            origin: leadForm.origin,
            status: leadForm.status,
            notes: leadForm.notes || undefined,
          })
        : await createCrmLead({
            name: leadForm.name,
            phone: leadForm.phone || undefined,
            email: leadForm.email || undefined,
            origin: leadForm.origin,
            status: leadForm.status,
            notes: leadForm.notes || undefined,
          });
      setEditingLeadId(null);
      setLeadForm({ name: "", phone: "", email: "", origin: "manual", status: "Novo lead", notes: "" });
      setSelectedLeadId(lead.id);
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar lead");
    } finally {
      setSaving("");
    }
  }

  async function handleDeleteLead() {
    if (!selectedLead) return;
    setSaving("lead-delete");
    setError("");
    try {
      await deleteCrmLead(selectedLead.id);
      setEditingLeadId(null);
      setSelectedLeadId(null);
      setLeadForm({ name: "", phone: "", email: "", origin: "manual", status: "Novo lead", notes: "" });
      setLeadActivity([]);
      await refreshAfterMutation({ keepLead: false, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir lead");
    } finally {
      setSaving("");
    }
  }

  async function handleUpdateLeadStatus(status: string) {
    if (!selectedLead) return;
    setSaving("lead-status");
    setError("");
    try {
      await updateCrmLead(selectedLead.id, { status });
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
      setLeadActivity(await getCrmLeadActivity(selectedLead.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar lead");
    } finally {
      setSaving("");
    }
  }

  async function handleCreateFollowup(event: FormEvent) {
    event.preventDefault();
    if (!selectedLead) return;
    setSaving("followup");
    setError("");
    try {
      if (editingFollowupId) {
        await updateCrmFollowup(editingFollowupId, {
          title: followupForm.title,
          description: followupForm.description || undefined,
          due_at: new Date(followupForm.due_at).toISOString(),
          channel: followupForm.channel,
          status: followupForm.status,
        });
      } else {
        await createCrmFollowup({
          lead_id: selectedLead.id,
          title: followupForm.title,
          description: followupForm.description || undefined,
          due_at: new Date(followupForm.due_at).toISOString(),
          channel: followupForm.channel,
          status: followupForm.status,
        });
      }
      setEditingFollowupId(null);
      setFollowupForm({ title: "", description: "", due_at: "", channel: "whatsapp", status: "pendente" });
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
      setLeadActivity(await getCrmLeadActivity(selectedLead.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar follow-up");
    } finally {
      setSaving("");
    }
  }

  async function handleCreateTask(event: FormEvent) {
    event.preventDefault();
    setSaving("task");
    setError("");
    try {
      if (editingTaskId) {
        await updateCrmTask(editingTaskId, {
          title: taskForm.title,
          description: taskForm.description || undefined,
          due_at: taskForm.due_at ? new Date(taskForm.due_at).toISOString() : null,
          priority: taskForm.priority,
          status: taskForm.status,
          lead_id: selectedLead?.id ?? null,
        });
      } else {
        await createCrmTask({
          title: taskForm.title,
          description: taskForm.description || undefined,
          due_at: taskForm.due_at ? new Date(taskForm.due_at).toISOString() : undefined,
          priority: taskForm.priority,
          status: taskForm.status,
          lead_id: selectedLead?.id ?? null,
        });
      }
      setEditingTaskId(null);
      setTaskForm({ title: "", description: "", due_at: "", priority: "media", status: "pendente" });
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar tarefa");
    } finally {
      setSaving("");
    }
  }

  async function handleDeleteFollowup(followupId: number) {
    setSaving("followup-delete");
    setError("");
    try {
      await deleteCrmFollowup(followupId);
      if (editingFollowupId === followupId) {
        setEditingFollowupId(null);
        setFollowupForm({ title: "", description: "", due_at: "", channel: "whatsapp", status: "pendente" });
      }
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir follow-up");
    } finally {
      setSaving("");
    }
  }

  async function handleDeleteTask(taskId: number) {
    setSaving("task-delete");
    setError("");
    try {
      await deleteCrmTask(taskId);
      if (editingTaskId === taskId) {
        setEditingTaskId(null);
        setTaskForm({ title: "", description: "", due_at: "", priority: "media", status: "pendente" });
      }
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir tarefa");
    } finally {
      setSaving("");
    }
  }

  async function handleSendCrmMessage(event: FormEvent) {
    event.preventDefault();
    if (!selectedConversation || !messageDraft.trim()) return;
    setSaving("message");
    setError("");
    try {
      await sendCrmConversationMessage(selectedConversation.id, messageDraft);
      setMessageDraft("");
      setCrmMessages(await getCrmMessages(selectedConversation.id));
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar mensagem");
    } finally {
      setSaving("");
    }
  }

  async function handleConversationAction(payload: { assigned_user_id?: number | null; ai_enabled?: boolean; status?: string }) {
    if (!selectedConversation) return;
    setSaving("conversation");
    setError("");
    try {
      const updated = await updateCrmConversationState(selectedConversation.id, payload);
      setSelectedConversationId(updated.id);
      if (updated.lead_id) {
        setSelectedLeadId(updated.lead_id);
      }
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar conversa");
    } finally {
      setSaving("");
    }
  }

  async function handleMoveLeadToColumn(leadId: number, status: string) {
    setSaving("kanban");
    setError("");
    try {
      await moveCrmKanban(leadId, status);
      setSelectedLeadId(leadId);
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao mover lead no kanban");
    } finally {
      setSaving("");
      setDragLeadId(null);
      setDragOverColumn(null);
    }
  }

  async function handleSaveWhatsAppConnection(event: FormEvent) {
    event.preventDefault();
    setSaving("whatsapp-save");
    setError("");
    try {
      const connection = await upsertCrmWhatsAppConnection({
        provider: whatsAppForm.provider,
        instance_name: whatsAppForm.instance_name,
        api_base_url: whatsAppForm.api_base_url || null,
        api_key: whatsAppForm.api_key || null,
        webhook_url: whatsAppForm.webhook_url || null,
      });
      setWhatsAppConnection(connection);
      setWhatsAppStatus({
        status: connection.status,
        connected_phone: connection.connected_phone,
        qr_code_base64: connection.qr_code_base64,
        raw: null,
      });
      setWhatsAppForm((current) => ({ ...current, api_key: "" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar conexão WhatsApp");
    } finally {
      setSaving("");
    }
  }

  async function handleConnectWhatsApp() {
    setSaving("whatsapp-connect");
    setError("");
    try {
      const status = await connectCrmWhatsApp();
      setWhatsAppStatus(status);
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao conectar WhatsApp");
    } finally {
      setSaving("");
    }
  }

  async function handleRefreshWhatsAppStatus() {
    setSaving("whatsapp-status");
    setError("");
    try {
      const status = await getCrmWhatsAppStatus();
      setWhatsAppStatus(status);
      setWhatsAppConnection(await getCrmWhatsAppConnection());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao consultar status do WhatsApp");
    } finally {
      setSaving("");
    }
  }

  async function handleFetchWhatsAppQr() {
    setSaving("whatsapp-qr");
    setError("");
    try {
      const status = await getCrmWhatsAppQrCode();
      setWhatsAppStatus(status);
      setWhatsAppConnection(await getCrmWhatsAppConnection());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao buscar QR Code");
    } finally {
      setSaving("");
    }
  }

  async function handleDisconnectWhatsApp() {
    setSaving("whatsapp-disconnect");
    setError("");
    try {
      await disconnectCrmWhatsApp();
      setWhatsAppStatus({ status: "disconnected", connected_phone: null, qr_code_base64: null, raw: null });
      setWhatsAppConnection(await getCrmWhatsAppConnection());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desconectar WhatsApp");
    } finally {
      setSaving("");
    }
  }

  async function handleUpdateSettings(event: FormEvent) {
    event.preventDefault();
    setSaving("settings");
    setError("");
    try {
      await updateCrmSettings({
        initial_auto_message: settingsForm.initial_auto_message,
        status_options: settingsForm.status_options
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        tags: settingsForm.tags
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        hermes_enabled: settingsForm.hermes_enabled,
      });
      await refreshAfterMutation({ keepLead: true, keepConversation: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar configuração");
    } finally {
      setSaving("");
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] bg-[linear-gradient(135deg,#17362f,#245548_55%,#eedfc3)] p-8 text-white shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-white/60">CRM</div>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-serif text-4xl">Operação comercial unificada</h2>
            <p className="mt-3 max-w-2xl text-sm text-white/75">
              Leads, kanban, follow-ups, histórico e atendimento manual centralizados sobre a base existente de
              Telegram, Hermes e créditos.
            </p>
          </div>
          <div className="rounded-3xl border border-white/15 bg-white/10 px-5 py-4 text-sm">
            Hermes no CRM: {settings?.hermes_enabled ? "ativo" : "desativado"}
          </div>
        </div>
      </div>

      {error ? <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {summaryCards.map((card) => (
          <div key={card.label} className="rounded-[28px] bg-white/85 p-5 shadow-soft">
            <div className="text-sm text-slate-500">{card.label}</div>
            <div className="mt-2 text-3xl font-semibold text-ink">{card.value}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr,0.95fr]">
        <section className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between gap-4">
            <h3 className="font-serif text-2xl">Leads</h3>
            <input className="input max-w-xs" placeholder="Buscar lead" value={filter} onChange={(e) => setFilter(e.target.value)} />
          </div>
          <div className="mt-5 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-slate-400">
                <tr>
                  <th className="px-3 py-3 font-medium">Nome</th>
                  <th className="px-3 py-3 font-medium">Origem</th>
                  <th className="px-3 py-3 font-medium">Status</th>
                  <th className="px-3 py-3 font-medium">Último contato</th>
                </tr>
              </thead>
              <tbody>
                {filteredLeads.map((lead) => (
                  <tr
                    key={lead.id}
                    onClick={() => setSelectedLeadId(lead.id)}
                    className={`cursor-pointer border-t border-black/5 ${selectedLead?.id === lead.id ? "bg-brand/5" : ""}`}
                  >
                    <td className="px-3 py-4">
                      <div className="font-medium">{lead.name}</div>
                      <div className="text-slate-500">{lead.phone || lead.email || "-"}</div>
                    </td>
                    <td className="px-3 py-4 text-slate-700">{lead.origin}</td>
                    <td className="px-3 py-4">
                      <span className="rounded-full bg-brand/10 px-3 py-1 text-xs text-brand">{lead.status}</span>
                    </td>
                    <td className="px-3 py-4 text-slate-700">{formatDateTime(lead.last_contact_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between gap-4">
            <h3 className="font-serif text-2xl">Lead selecionado</h3>
            <div className="text-sm text-slate-500">{selectedLead ? `#${selectedLead.id}` : "Nenhum lead"}</div>
          </div>
          {selectedLead ? (
            <div className="mt-5 space-y-4 text-sm text-slate-700">
              <div className="rounded-2xl bg-panel px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-medium text-ink">{selectedLead.name}</div>
                    <div>{selectedLead.phone || selectedLead.email || "-"}</div>
                    <div className="mt-1 text-slate-500">Origem: {selectedLead.origin}</div>
                    <div className="mt-1 text-slate-500">Status: {selectedLead.status}</div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingLeadId(selectedLead.id);
                        setLeadForm({
                          name: selectedLead.name,
                          phone: selectedLead.phone || "",
                          email: selectedLead.email || "",
                          origin: selectedLead.origin,
                          status: selectedLead.status,
                          notes: selectedLead.notes || "",
                        });
                      }}
                      className="rounded-2xl bg-white px-3 py-2 text-xs text-slate-700"
                    >
                      Editar
                    </button>
                    <button
                      onClick={handleDeleteLead}
                      className="rounded-2xl bg-red-100 px-3 py-2 text-xs text-red-700"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
                <div className="mt-3 text-slate-600">{selectedLead.notes || "Sem observações"}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(settings?.status_options || []).map((statusName) => (
                    <button
                      key={statusName}
                      onClick={() => handleUpdateLeadStatus(statusName)}
                      className="rounded-full bg-white px-3 py-1 text-xs text-slate-600 shadow-sm"
                    >
                      {statusName}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-2 text-xs uppercase tracking-[0.2em] text-slate-400">Timeline</div>
                <div className="space-y-3">
                  {leadActivity.slice(0, 6).map((item) => (
                    <div key={item.id} className="rounded-2xl border border-black/5 px-4 py-3">
                      <div className="font-medium text-ink">{item.action}</div>
                      <div className="text-slate-600">{item.description || "Sem descrição"}</div>
                      <div className="mt-1 text-xs text-slate-400">{formatDateTime(item.created_at)}</div>
                    </div>
                  ))}
                  {leadActivity.length === 0 ? <div className="text-slate-500">Sem histórico para este lead.</div> : null}
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-5 text-sm text-slate-500">Selecione um lead para ver detalhes e histórico.</div>
          )}
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
        <section className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="flex items-center justify-between gap-4">
            <h3 className="font-serif text-2xl">Kanban</h3>
            <div className="text-sm text-slate-500">Arraste o card para outra coluna</div>
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-3">
            {kanban?.columns.map((column) => (
              <div
                key={column.id}
                onDragOver={(event) => {
                  event.preventDefault();
                  if (dragLeadId !== null) {
                    setDragOverColumn(column.name);
                  }
                }}
                onDragLeave={() => {
                  if (dragOverColumn === column.name) {
                    setDragOverColumn(null);
                  }
                }}
                onDrop={async (event) => {
                  event.preventDefault();
                  const leadId = Number(event.dataTransfer.getData("text/plain") || dragLeadId);
                  if (!leadId) return;
                  await handleMoveLeadToColumn(leadId, column.name);
                }}
                className={`rounded-[24px] p-4 transition ${
                  dragOverColumn === column.name ? "bg-brand/15 ring-2 ring-brand/30" : "bg-panel"
                }`}
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="font-medium text-ink">{column.name}</div>
                  <div className="rounded-full bg-white px-2 py-1 text-xs text-slate-500">
                    {kanban.cards[column.name]?.length || 0}
                  </div>
                </div>
                <div className="space-y-3">
                  {(kanban.cards[column.name] || []).slice(0, 5).map((card) => (
                    <button
                      key={card.lead.id}
                      draggable
                      onDragStart={(event) => {
                        event.dataTransfer.setData("text/plain", String(card.lead.id));
                        event.dataTransfer.effectAllowed = "move";
                        setSelectedLeadId(card.lead.id);
                        setDragLeadId(card.lead.id);
                      }}
                      onDragEnd={() => {
                        setDragLeadId(null);
                        setDragOverColumn(null);
                      }}
                      onClick={() => {
                        setSelectedLeadId(card.lead.id);
                        if (card.conversation?.id) {
                          setSelectedConversationId(card.conversation.id);
                        }
                      }}
                      className={`w-full rounded-2xl bg-white px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 ${
                        dragLeadId === card.lead.id ? "opacity-60 ring-2 ring-brand/30" : ""
                      }`}
                    >
                      <div className="font-medium">{card.lead.name}</div>
                      <div className="mt-1 text-sm text-slate-500">{card.lead.phone || card.lead.email || "-"}</div>
                      <div className="mt-2 text-xs text-slate-400">{card.conversation?.last_message || "Sem conversa recente"}</div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-6">
          <div className="rounded-[32px] bg-white p-6 shadow-soft">
            <h3 className="font-serif text-2xl">{editingLeadId ? "Editar lead" : "Novo lead manual"}</h3>
            <form onSubmit={handleCreateLead} className="mt-5 grid gap-3">
              <input className="input" placeholder="Nome" value={leadForm.name} onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })} />
              <div className="grid gap-3 md:grid-cols-2">
                <input className="input" placeholder="Telefone" value={leadForm.phone} onChange={(e) => setLeadForm({ ...leadForm, phone: e.target.value })} />
                <input className="input" placeholder="Email" value={leadForm.email} onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })} />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <input className="input" placeholder="Origem" value={leadForm.origin} onChange={(e) => setLeadForm({ ...leadForm, origin: e.target.value })} />
                <input className="input" placeholder="Status" value={leadForm.status} onChange={(e) => setLeadForm({ ...leadForm, status: e.target.value })} />
              </div>
              <textarea className="input min-h-24" placeholder="Observações" value={leadForm.notes} onChange={(e) => setLeadForm({ ...leadForm, notes: e.target.value })} />
              <div className="flex gap-3">
                <button disabled={saving === "lead"} className="rounded-2xl bg-brand px-4 py-3 font-medium text-white">
                  {saving === "lead" ? "Salvando..." : editingLeadId ? "Salvar lead" : "Criar lead"}
                </button>
                {editingLeadId ? (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingLeadId(null);
                      setLeadForm({ name: "", phone: "", email: "", origin: "manual", status: "Novo lead", notes: "" });
                    }}
                    className="rounded-2xl bg-slate-200 px-4 py-3 font-medium text-slate-700"
                  >
                    Cancelar
                  </button>
                ) : null}
              </div>
            </form>
          </div>

          <div className="rounded-[32px] bg-white p-6 shadow-soft">
            <h3 className="font-serif text-2xl">{editingFollowupId ? "Editar follow-up" : "Follow-up rápido"}</h3>
            <form onSubmit={handleCreateFollowup} className="mt-5 grid gap-3">
              <input className="input" placeholder="Título" value={followupForm.title} onChange={(e) => setFollowupForm({ ...followupForm, title: e.target.value })} />
              <textarea className="input min-h-20" placeholder="Descrição" value={followupForm.description} onChange={(e) => setFollowupForm({ ...followupForm, description: e.target.value })} />
              <div className="grid gap-3 md:grid-cols-3">
                <input className="input" type="datetime-local" value={followupForm.due_at} onChange={(e) => setFollowupForm({ ...followupForm, due_at: e.target.value })} />
                <input className="input" placeholder="Canal" value={followupForm.channel} onChange={(e) => setFollowupForm({ ...followupForm, channel: e.target.value })} />
                <select className="input" value={followupForm.status} onChange={(e) => setFollowupForm({ ...followupForm, status: e.target.value })}>
                  <option value="pendente">Pendente</option>
                  <option value="feito">Feito</option>
                  <option value="atrasado">Atrasado</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button disabled={saving === "followup" || !selectedLead} className="rounded-2xl bg-ink px-4 py-3 font-medium text-white">
                  {saving === "followup" ? "Salvando..." : editingFollowupId ? "Salvar follow-up" : "Criar follow-up"}
                </button>
                {editingFollowupId ? (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingFollowupId(null);
                      setFollowupForm({ title: "", description: "", due_at: "", channel: "whatsapp", status: "pendente" });
                    }}
                    className="rounded-2xl bg-slate-200 px-4 py-3 font-medium text-slate-700"
                  >
                    Cancelar
                  </button>
                ) : null}
              </div>
            </form>
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px,1fr,360px]">
        <section className="overflow-hidden rounded-[32px] bg-white shadow-soft">
          <div className="border-b border-black/5 px-5 py-4">
            <h3 className="font-serif text-2xl">Conversas</h3>
          </div>
          <div className="max-h-[620px] overflow-y-auto">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => {
                  setSelectedConversationId(conversation.id);
                  if (conversation.lead_id) {
                    setSelectedLeadId(conversation.lead_id);
                  }
                }}
                className={`w-full border-b border-black/5 px-5 py-4 text-left transition ${
                  selectedConversationId === conversation.id ? "bg-brand/10" : "hover:bg-panel"
                }`}
              >
                <div className="font-medium">{conversation.contact_name || "Contato"}</div>
                <div className="text-sm text-slate-500">{conversation.last_message || "Sem mensagens"}</div>
                <div className="mt-2 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-slate-400">
                  <span>{conversation.channel}</span>
                  <span>{conversation.ai_enabled ? "IA ativa" : "IA pausada"}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="overflow-hidden rounded-[32px] bg-white shadow-soft">
          <div className="border-b border-black/5 px-6 py-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="font-medium text-ink">{selectedConversation?.contact_name || "Selecione uma conversa"}</div>
                <div className="text-sm text-slate-500">{selectedConversation?.contact_phone || selectedConversation?.external_id || ""}</div>
              </div>
              {selectedConversation ? (
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleConversationAction({ assigned_user_id: profile.user.id, ai_enabled: false, status: "human" })}
                    className="rounded-2xl bg-ink px-3 py-2 text-xs text-white"
                  >
                    Assumir
                  </button>
                  <button
                    onClick={() => handleConversationAction({ ai_enabled: true, status: "open" })}
                    className="rounded-2xl bg-brand px-3 py-2 text-xs text-white"
                  >
                    Devolver para IA
                  </button>
                  <button
                    onClick={() => handleConversationAction({ status: "resolved" })}
                    className="rounded-2xl bg-slate-200 px-3 py-2 text-xs text-slate-700"
                  >
                    Resolver
                  </button>
                </div>
              ) : null}
            </div>
          </div>
          <div className="max-h-[520px] overflow-y-auto bg-[linear-gradient(180deg,#f7f4ed,#efe8dc)] p-6">
            <div className="space-y-4">
              {crmMessages.map((message) => (
                <div
                  key={message.id}
                  className={`max-w-[75%] rounded-[22px] px-4 py-3 text-sm shadow ${
                    message.sender_type === "user" ? "bg-white" : "ml-auto bg-bubble"
                  }`}
                >
                  {message.content}
                </div>
              ))}
            </div>
          </div>
          <form onSubmit={handleSendCrmMessage} className="border-t border-black/5 bg-white/90 p-4">
            <div className="flex gap-3">
              <input className="input flex-1" placeholder="Responder pelo CRM" value={messageDraft} onChange={(e) => setMessageDraft(e.target.value)} />
              <button disabled={saving === "message" || !selectedConversation} className="rounded-2xl bg-brand px-5 py-3 font-medium text-white">
                {saving === "message" ? "Enviando..." : "Enviar"}
              </button>
            </div>
          </form>
        </section>

        <section className="grid gap-6">
          <div className="rounded-[32px] bg-white p-6 shadow-soft">
            <h3 className="font-serif text-2xl">Tarefas CRM</h3>
            <form onSubmit={handleCreateTask} className="mt-5 grid gap-3">
              <input className="input" placeholder="Título" value={taskForm.title} onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })} />
              <textarea className="input min-h-20" placeholder="Descrição" value={taskForm.description} onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })} />
              <div className="grid gap-3 md:grid-cols-3">
                <input className="input" type="datetime-local" value={taskForm.due_at} onChange={(e) => setTaskForm({ ...taskForm, due_at: e.target.value })} />
                <select className="input" value={taskForm.priority} onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}>
                  <option value="baixa">Baixa</option>
                  <option value="media">Média</option>
                  <option value="alta">Alta</option>
                </select>
                <select className="input" value={taskForm.status} onChange={(e) => setTaskForm({ ...taskForm, status: e.target.value })}>
                  <option value="pendente">Pendente</option>
                  <option value="em_andamento">Em andamento</option>
                  <option value="feito">Feito</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button disabled={saving === "task"} className="rounded-2xl bg-ink px-4 py-3 font-medium text-white">
                  {saving === "task" ? "Salvando..." : editingTaskId ? "Salvar tarefa" : "Criar tarefa"}
                </button>
                {editingTaskId ? (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingTaskId(null);
                      setTaskForm({ title: "", description: "", due_at: "", priority: "media", status: "pendente" });
                    }}
                    className="rounded-2xl bg-slate-200 px-4 py-3 font-medium text-slate-700"
                  >
                    Cancelar
                  </button>
                ) : null}
              </div>
            </form>
            <div className="mt-5 space-y-3">
              {crmTasks.slice(0, 5).map((task) => (
                <div key={task.id} className="rounded-2xl bg-panel px-4 py-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{task.title}</div>
                    <span className="rounded-full bg-white px-2 py-1 text-xs uppercase text-slate-500">{task.priority}</span>
                  </div>
                  <div className="mt-1 text-sm text-slate-600">{task.description || "Sem descrição"}</div>
                  <div className="mt-2 text-xs text-slate-400">{formatDateTime(task.due_at)}</div>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => {
                        setEditingTaskId(task.id);
                        setTaskForm({
                          title: task.title,
                          description: task.description || "",
                          due_at: task.due_at ? new Date(task.due_at).toISOString().slice(0, 16) : "",
                          priority: task.priority,
                          status: task.status,
                        });
                      }}
                      className="rounded-2xl bg-white px-3 py-2 text-xs text-slate-700"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDeleteTask(task.id)}
                      className="rounded-2xl bg-red-100 px-3 py-2 text-xs text-red-700"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[32px] bg-white p-6 shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-serif text-2xl">Conectar WhatsApp</h3>
              <span className="rounded-full bg-panel px-3 py-1 text-xs uppercase text-slate-600">
                {whatsAppStatus?.status || whatsAppConnection?.status || "disconnected"}
              </span>
            </div>
            <form onSubmit={handleSaveWhatsAppConnection} className="mt-5 grid gap-3">
              <select
                className="input"
                value={whatsAppForm.provider}
                onChange={(e) => setWhatsAppForm({ ...whatsAppForm, provider: e.target.value })}
              >
                <option value="evolution_go">Evolution Go</option>
              </select>
              <input
                className="input"
                placeholder="Nome da instância"
                value={whatsAppForm.instance_name}
                onChange={(e) => setWhatsAppForm({ ...whatsAppForm, instance_name: e.target.value })}
              />
              <input
                className="input"
                placeholder="URL base da API"
                value={whatsAppForm.api_base_url}
                onChange={(e) => setWhatsAppForm({ ...whatsAppForm, api_base_url: e.target.value })}
              />
              <input
                className="input"
                placeholder="API key"
                value={whatsAppForm.api_key}
                onChange={(e) => setWhatsAppForm({ ...whatsAppForm, api_key: e.target.value })}
              />
              <input
                className="input"
                placeholder="Webhook URL"
                value={whatsAppForm.webhook_url}
                onChange={(e) => setWhatsAppForm({ ...whatsAppForm, webhook_url: e.target.value })}
              />
              <div className="grid gap-3 md:grid-cols-2">
                <button disabled={saving === "whatsapp-save"} className="rounded-2xl bg-brand px-4 py-3 font-medium text-white">
                  {saving === "whatsapp-save" ? "Salvando..." : "Salvar conexão"}
                </button>
                <button
                  type="button"
                  onClick={handleConnectWhatsApp}
                  disabled={saving === "whatsapp-connect" || !whatsAppConnection}
                  className="rounded-2xl bg-ink px-4 py-3 font-medium text-white"
                >
                  {saving === "whatsapp-connect" ? "Conectando..." : "Conectar"}
                </button>
              </div>
            </form>

            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <button
                type="button"
                onClick={handleRefreshWhatsAppStatus}
                disabled={!whatsAppConnection || saving === "whatsapp-status"}
                className="rounded-2xl bg-slate-200 px-4 py-3 text-sm font-medium text-slate-700"
              >
                {saving === "whatsapp-status" ? "Consultando..." : "Atualizar status"}
              </button>
              <button
                type="button"
                onClick={handleFetchWhatsAppQr}
                disabled={!whatsAppConnection || saving === "whatsapp-qr"}
                className="rounded-2xl bg-slate-200 px-4 py-3 text-sm font-medium text-slate-700"
              >
                {saving === "whatsapp-qr" ? "Buscando..." : "Gerar QR"}
              </button>
              <button
                type="button"
                onClick={handleDisconnectWhatsApp}
                disabled={!whatsAppConnection || saving === "whatsapp-disconnect"}
                className="rounded-2xl bg-red-100 px-4 py-3 text-sm font-medium text-red-700"
              >
                {saving === "whatsapp-disconnect" ? "Desconectando..." : "Desconectar"}
              </button>
            </div>

            <div className="mt-5 rounded-2xl bg-panel px-4 py-4 text-sm text-slate-700">
              <div>Status: {whatsAppStatus?.status || whatsAppConnection?.status || "-"}</div>
              <div className="mt-1">Instância: {whatsAppConnection?.instance_name || "-"}</div>
              <div className="mt-1">Telefone: {whatsAppStatus?.connected_phone || whatsAppConnection?.connected_phone || "-"}</div>
              <div className="mt-1">Erro: {whatsAppConnection?.last_error || "-"}</div>
              <div className="mt-1">Último evento webhook: {whatsAppConnection?.last_webhook_event || "-"}</div>
              <div className="mt-1">Último webhook em: {formatDateTime(whatsAppConnection?.last_webhook_at) || "-"}</div>
            </div>

            {whatsAppConnection?.last_webhook_payload ? (
              <div className="mt-5 rounded-[28px] border border-black/5 bg-white p-4">
                <div className="mb-3 text-xs uppercase tracking-[0.2em] text-slate-400">Último payload recebido</div>
                <pre className="max-h-72 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">
                  {whatsAppConnection.last_webhook_payload}
                </pre>
              </div>
            ) : null}

            {whatsAppQrCodeSrc ? (
              <div className="mt-5 rounded-[28px] border border-black/5 bg-white p-4">
                <div className="mb-3 text-xs uppercase tracking-[0.2em] text-slate-400">QR Code</div>
                <img src={whatsAppQrCodeSrc} alt="QR Code do WhatsApp" className="mx-auto w-full max-w-[260px] rounded-2xl border border-black/5 bg-white p-3" />
              </div>
            ) : null}
          </div>

          <div className="rounded-[32px] bg-ink p-6 text-white shadow-soft">
            <h3 className="font-serif text-2xl">Configuração do CRM</h3>
            <form onSubmit={handleUpdateSettings} className="mt-5 grid gap-3 text-sm">
              <textarea
                className="input min-h-20 bg-white text-slate-800"
                placeholder="Mensagem automática inicial"
                value={settingsForm.initial_auto_message}
                onChange={(e) => setSettingsForm({ ...settingsForm, initial_auto_message: e.target.value })}
              />
              <input
                className="input bg-white text-slate-800"
                placeholder="Status separados por vírgula"
                value={settingsForm.status_options}
                onChange={(e) => setSettingsForm({ ...settingsForm, status_options: e.target.value })}
              />
              <input
                className="input bg-white text-slate-800"
                placeholder="Tags separadas por vírgula"
                value={settingsForm.tags}
                onChange={(e) => setSettingsForm({ ...settingsForm, tags: e.target.value })}
              />
              <label className="flex items-center gap-3 text-white/80">
                <input
                  type="checkbox"
                  checked={settingsForm.hermes_enabled}
                  onChange={(e) => setSettingsForm({ ...settingsForm, hermes_enabled: e.target.checked })}
                />
                Hermes habilitado no atendimento
              </label>
              <button disabled={saving === "settings"} className="rounded-2xl bg-white px-4 py-3 font-medium text-ink">
                {saving === "settings" ? "Salvando..." : "Salvar configuração"}
              </button>
            </form>
          </div>
        </section>
      </div>

      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h3 className="font-serif text-2xl">Follow-ups do dia</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {followups.length === 0 ? <div className="text-sm text-slate-500">Nenhum follow-up pendente hoje.</div> : null}
          {followups.map((followup) => (
            <div key={followup.id} className="rounded-2xl bg-panel px-4 py-4">
              <div className="flex items-center justify-between gap-3">
                <div className="font-medium text-ink">{followup.title}</div>
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{followup.channel}</div>
              </div>
              <div className="mt-1 text-sm text-slate-600">{followup.description || "Sem descrição"}</div>
              <div className="mt-2 text-xs text-slate-500">{formatDateTime(followup.due_at)}</div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => {
                    setEditingFollowupId(followup.id);
                    setFollowupForm({
                      title: followup.title,
                      description: followup.description || "",
                      due_at: new Date(followup.due_at).toISOString().slice(0, 16),
                      channel: followup.channel,
                      status: followup.status,
                    });
                    setSelectedLeadId(followup.lead_id);
                  }}
                  className="rounded-2xl bg-white px-3 py-2 text-xs text-slate-700"
                >
                  Editar
                </button>
                <button
                  onClick={() => handleDeleteFollowup(followup.id)}
                  className="rounded-2xl bg-red-100 px-3 py-2 text-xs text-red-700"
                >
                  Excluir
                </button>
              </div>
            </div>
          ))}
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
          }
        />
        <Route path="/crm" element={<CrmWorkspace profile={profile} />} />
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
