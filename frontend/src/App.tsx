import { FormEvent, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { getChats, getCredits, getLeads, getMessages, getTasks, login, me, sendMessage, toggleAi } from "./api";
import type { Chat, Credit, Lead, MeResponse, Message, Task } from "./types";

function currencyCredits(credits?: Credit) {
  if (!credits) return "--";
  return `${credits.remaining}/${credits.total}`;
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
    { label: "Leads", path: "/leads" },
    { label: "Tarefas", path: "/tasks" },
    { label: "Créditos", path: "/credits" },
    { label: "Configurações", path: "/settings" },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#f7fbf6,transparent_35%),linear-gradient(135deg,#e2f2ea,#f4efe6)] text-ink">
      <div className="mx-auto flex min-h-screen max-w-[1500px]">
        <aside className="w-72 border-r border-black/5 bg-white/70 p-6 backdrop-blur-xl">
          <div className="mb-10">
            <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Hermes Agente</div>
            <h1 className="mt-2 font-serif text-3xl font-semibold">Painel SaaS</h1>
            <p className="mt-3 text-sm text-slate-600">{profile.tenant.name}</p>
          </div>

          <nav className="space-y-2">
            {nav.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full rounded-2xl px-4 py-3 text-left text-sm transition ${
                  location.pathname === item.path
                    ? "bg-brand text-white shadow-soft"
                    : "bg-white text-slate-700 hover:bg-brand/10"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="mt-10 rounded-3xl bg-ink p-5 text-sm text-white">
            <div className="text-white/60">Operador</div>
            <div className="mt-2 font-medium">{profile.user.name}</div>
            <div className="text-white/70">{profile.user.role}</div>
          </div>
        </aside>

        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}

function LoginPage({ onLogged }: { onLogged: () => void }) {
  const [email, setEmail] = useState("admin@empresa.com");
  const [password, setPassword] = useState("123456");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    try {
      const result = await login(email, password);
      localStorage.setItem("hermes_token", result.access_token);
      onLogged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(140deg,#1b7f6b,#163b32_55%,#f1e9dc)] p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-md rounded-[32px] bg-white p-8 shadow-soft">
        <div className="text-xs uppercase tracking-[0.3em] text-brand/70">Telegram + DeepSeek</div>
        <h1 className="mt-3 font-serif text-4xl font-semibold text-ink">Entrar</h1>
        <p className="mt-3 text-sm text-slate-500">Painel estilo WhatsApp com CRM e operação multi-tenant.</p>
        <div className="mt-8 space-y-4">
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
            <div>Canal: Telegram com resposta por DeepSeek.</div>
            <div>Estado: pronto para receber onboarding e deploy em Coolify.</div>
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
          <div>Engine IA: DeepSeek</div>
          <div>Modo de atendimento: híbrido IA + humano</div>
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

