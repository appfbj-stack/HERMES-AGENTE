import { FormEvent, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { getChats, getCredits, getLeads, getMessages, getTasks, login, me, sendMessage, toggleAi } from "./api";
import type { Chat, Credit, Lead, MeResponse, Message, Task } from "./types";

function currencyCredits(credits?: Credit) {
  if (!credits) return "--";
  return `${credits.remaining.toLocaleString("pt-BR")} / ${credits.total.toLocaleString("pt-BR")}`;
}

function Layout({
  profile,
  credits,
  children,
}: {
  profile: MeResponse;
  credits?: Credit;
  children: React.ReactNode;
}) {
  const location = useLocation();
  const navigate = useNavigate();

  const nav = [
    { label: "Dashboard", path: "/dashboard" },
    { label: "Chat", path: "/chat" },
    { label: "Leads", path: "/leads" },
    { label: "Tarefas", path: "/tasks" },
    { label: "Mensagens", path: "/credits" },
    { label: "Configurações", path: "/settings" },
  ];

  const remaining = credits?.remaining ?? 0;
  const total = credits?.total ?? 0;
  const pct = total > 0 ? Math.max(0, Math.min(100, (remaining / total) * 100)) : 0;
  const isLow = total > 0 && remaining / total <= 0.1;
  const isBlocked = total > 0 && remaining <= 0;

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

          <div
            onClick={() => navigate("/credits")}
            className={`mt-6 cursor-pointer rounded-3xl p-5 text-sm transition ${
              isBlocked
                ? "bg-red-600 text-white"
                : isLow
                  ? "bg-amber-500 text-white"
                  : "bg-emerald-600 text-white"
            }`}
          >
            <div className="text-white/80 text-xs uppercase tracking-wider">Mensagens</div>
            <div className="mt-1 text-2xl font-semibold">
              {remaining.toLocaleString("pt-BR")}
              <span className="text-sm text-white/70">/{total.toLocaleString("pt-BR")}</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/30">
              <div className="h-full bg-white" style={{ width: `${pct}%` }} />
            </div>
            {isBlocked && (
              <div className="mt-2 text-xs">
                ⚠️ Sem mensagens. Clique para comprar.
              </div>
            )}
            {isLow && !isBlocked && (
              <div className="mt-2 text-xs">⚠️ Acabando! Clique para comprar.</div>
            )}
          </div>

          <div className="mt-4 rounded-3xl bg-ink p-5 text-sm text-white">
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
    { label: "Mensagens", value: currencyCredits(credits) },
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
      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <h2 className="font-serif text-2xl">Atividade recente</h2>
        <div className="mt-5 space-y-3">
          {chats.length === 0 && (
            <div className="rounded-2xl bg-panel px-4 py-6 text-center text-sm text-slate-500">
              Nenhuma conversa ainda. Quando seu bot receber a primeira mensagem, aparecerá aqui.
            </div>
          )}
          {chats.slice(0, 8).map((chat) => {
            const initials = (chat.contact_name || "?")
              .split(" ")
              .map((n) => n[0])
              .slice(0, 2)
              .join("")
              .toUpperCase();
            return (
              <div
                key={chat.id}
                className="flex items-center gap-3 rounded-2xl bg-panel px-4 py-3"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white">
                  {initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-medium">
                      {chat.contact_name || "Sem nome"}
                    </span>
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] uppercase text-emerald-700">
                      {chat.channel || "telegram"}
                    </span>
                  </div>
                  <div className="truncate text-sm text-slate-500">
                    {chat.last_message || "Sem mensagens"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ChatPage({
  chats,
  selectedChat,
  messages,
  credits,
  onSelectChat,
  onSendMessage,
  onToggleAi,
}: {
  chats: Chat[];
  selectedChat?: Chat;
  messages: Message[];
  credits?: Credit;
  onSelectChat: (chat: Chat) => void;
  onSendMessage: (content: string) => Promise<void>;
  onToggleAi: () => Promise<void>;
}) {
  const [content, setContent] = useState("");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const isBlocked = (credits?.remaining ?? 0) <= 0 && (credits?.total ?? 0) > 0;

  const filteredChats = chats.filter((c) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      (c.contact_name || "").toLowerCase().includes(q) ||
      (c.contact_phone || "").toLowerCase().includes(q) ||
      (c.last_message || "").toLowerCase().includes(q)
    );
  });

  function getInitials(name: string | null | undefined) {
    return (name || "?")
      .split(" ")
      .map((n) => n[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }

  function formatTime(iso?: string | null) {
    if (!iso) return "";
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) {
      return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    }
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return "Ontem";
    return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!content.trim() || isBlocked) return;
    await onSendMessage(content);
    setContent("");
  }

  return (
    <div className="grid h-[calc(100vh-3rem)] overflow-hidden rounded-[24px] bg-white shadow-soft xl:grid-cols-[360px,1fr]">
      {/* Sidebar de conversas */}
      <section className="flex flex-col overflow-hidden border-r border-black/5">
        <div className="border-b border-black/5 bg-[#f0f2f5] px-4 py-3">
          <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-2">
            <svg className="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
            </svg>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar conversa"
              className="flex-1 bg-transparent text-sm outline-none"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filteredChats.length === 0 && (
            <div className="px-6 py-12 text-center text-sm text-slate-400">
              Nenhuma conversa
            </div>
          )}
          {filteredChats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => onSelectChat(chat)}
              className={`flex w-full items-center gap-3 border-b border-black/5 px-4 py-3 text-left transition hover:bg-[#f5f6f6] ${
                selectedChat?.id === chat.id ? "bg-[#f0f2f5]" : ""
              }`}
            >
              <div className="relative shrink-0">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600 text-sm font-semibold text-white">
                  {getInitials(chat.contact_name)}
                </div>
                {!chat.ai_paused && (
                  <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate font-medium text-ink">{chat.contact_name || "Contato"}</span>
                  <span className="shrink-0 text-[11px] text-slate-400">{formatTime(chat.last_message_at)}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm text-slate-500">{chat.last_message || "Sem mensagens"}</span>
                  {chat.ai_paused && (
                    <span className="shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-amber-700">
                      Pausada
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Janela de conversa */}
      <section className="flex flex-col overflow-hidden">
        {selectedChat ? (
          <>
            {/* Header WhatsApp Web */}
            <div className="flex items-center justify-between border-b border-black/5 bg-[#f0f2f5] px-4 py-2.5">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-sm font-semibold text-white">
                    {getInitials(selectedChat.contact_name)}
                  </div>
                  {!selectedChat.ai_paused && (
                    <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-[#f0f2f5] bg-emerald-500" />
                  )}
                </div>
                <div>
                  <div className="font-medium text-ink">{selectedChat.contact_name || "Contato"}</div>
                  <div className="text-xs text-slate-500">
                    {selectedChat.contact_phone && <span>{selectedChat.contact_phone} · </span>}
                    {selectedChat.ai_paused ? "IA pausada" : "IA online"}
                  </div>
                </div>
              </div>
              <button
                onClick={onToggleAi}
                className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${
                  selectedChat.ai_paused
                    ? "bg-emerald-600 text-white hover:bg-emerald-700"
                    : "bg-amber-500 text-white hover:bg-amber-600"
                }`}
              >
                {selectedChat.ai_paused ? "▶ Retomar IA" : "⏸ Pausar IA"}
              </button>
            </div>

            {/* Mensagens com fundo estilo WhatsApp */}
            <div
              className="flex-1 overflow-y-auto px-6 py-4"
              style={{
                backgroundColor: "#efeae2",
                backgroundImage:
                  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill='%23000' fill-opacity='0.025'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z'/%3E%3C/g%3E%3C/svg%3E\")",
              }}
            >
              <div className="space-y-2">
                {messages.length === 0 && (
                  <div className="mx-auto mt-8 max-w-sm rounded-2xl bg-white/80 px-6 py-3 text-center text-sm text-slate-500 shadow-sm">
                    Sem mensagens nesta conversa.
                  </div>
                )}
                {messages.map((message) => {
                  const isClient = message.sender_type === "user";
                  const isHuman = message.sender_type === "human";
                  return (
                    <div
                      key={message.id}
                      className={`flex ${isClient ? "justify-start" : "justify-end"}`}
                    >
                      <div
                        className={`relative max-w-[78%] whitespace-pre-wrap break-words px-3 py-2 text-sm shadow-sm md:max-w-[60%] ${
                          isClient
                            ? "rounded-lg rounded-tl-none bg-white text-ink"
                            : isHuman
                              ? "rounded-lg rounded-tr-none bg-[#fff3c4] text-ink"
                              : "rounded-lg rounded-tr-none bg-[#d9fdd3] text-ink"
                        }`}
                      >
                        {!isClient && (
                          <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
                            {isHuman ? "Atendente" : "IA"}
                          </div>
                        )}
                        <div>{message.content}</div>
                        <div className="mt-1 text-right text-[10px] text-slate-500">
                          {formatTime(message.created_at)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            {isBlocked ? (
              <div className="border-t border-red-200 bg-red-50 p-4">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">🔒</div>
                  <div className="flex-1">
                    <div className="font-semibold text-red-900">Sem mensagens disponíveis</div>
                    <div className="text-xs text-red-700">A IA está pausada até você comprar mais.</div>
                  </div>
                  <button
                    onClick={() => navigate("/credits")}
                    className="rounded-2xl bg-red-600 px-5 py-2 text-sm font-semibold text-white hover:bg-red-700"
                  >
                    Comprar mensagens
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-black/5 bg-[#f0f2f5] px-3 py-2.5">
                <button type="button" className="p-2 text-slate-500 hover:text-slate-700" title="Emoji">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <button type="button" className="p-2 text-slate-500 hover:text-slate-700" title="Anexar">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>
                <input
                  className="flex-1 rounded-full bg-white px-4 py-2.5 text-sm outline-none ring-1 ring-black/5 focus:ring-emerald-500"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Digite uma mensagem"
                />
                <button
                  type="submit"
                  disabled={!content.trim()}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-white transition hover:bg-emerald-700 disabled:bg-slate-300"
                  title="Enviar"
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                  </svg>
                </button>
              </form>
            )}
          </>
        ) : (
          <div
            className="flex flex-1 flex-col items-center justify-center gap-3 text-slate-500"
            style={{
              backgroundColor: "#f0f2f5",
            }}
          >
            <div className="text-6xl">💬</div>
            <div className="text-lg font-medium">Hermes — Painel de atendimento</div>
            <div className="max-w-md text-center text-sm">
              Selecione uma conversa à esquerda para começar a atender. Mensagens recebidas pelo Telegram aparecerão automaticamente aqui.
            </div>
          </div>
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
  const total = credits?.total ?? 0;
  const used = credits?.used ?? 0;
  const remaining = credits?.remaining ?? 0;
  const pct = total > 0 ? Math.max(0, Math.min(100, (remaining / total) * 100)) : 0;
  const isBlocked = total > 0 && remaining <= 0;
  const isLow = total > 0 && remaining / total <= 0.1;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="text-sm text-slate-500">Plano (total)</div>
          <div className="mt-3 text-4xl font-semibold">{total.toLocaleString("pt-BR")}</div>
          <div className="mt-1 text-xs text-slate-400">mensagens/mês</div>
        </div>
        <div className="rounded-[32px] bg-white p-6 shadow-soft">
          <div className="text-sm text-slate-500">Usadas</div>
          <div className="mt-3 text-4xl font-semibold">{used.toLocaleString("pt-BR")}</div>
        </div>
        <div
          className={`rounded-[32px] p-6 shadow-soft text-white ${
            isBlocked ? "bg-red-600" : isLow ? "bg-amber-500" : "bg-ink"
          }`}
        >
          <div className="text-sm text-white/70">Restantes</div>
          <div className="mt-3 text-4xl font-semibold">{remaining.toLocaleString("pt-BR")}</div>
        </div>
      </div>

      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-slate-600">Consumo do mês</span>
          <span className="font-semibold">{pct.toFixed(0)}% restante</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full transition-all ${
              isBlocked ? "bg-red-600" : isLow ? "bg-amber-500" : "bg-emerald-600"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {isBlocked && (
        <div className="rounded-[32px] border-2 border-red-300 bg-red-50 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-600 text-2xl text-white">
              !
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900">
                Suas mensagens acabaram
              </h3>
              <p className="mt-1 text-sm text-red-700">
                A IA está pausada. Compre mais mensagens para voltar a atender automaticamente seus clientes.
              </p>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {[
              { label: "+500 mensagens", price: "R$ 49", qty: 500 },
              { label: "+2.000 mensagens", price: "R$ 149", qty: 2000, popular: true },
              { label: "+10.000 mensagens", price: "R$ 499", qty: 10000 },
            ].map((pkg) => (
              <button
                key={pkg.qty}
                onClick={() => alert(`Em breve: integração ASAAS para comprar ${pkg.label} por ${pkg.price}`)}
                className={`relative rounded-2xl border p-4 text-left transition hover:shadow-md ${
                  pkg.popular
                    ? "border-red-600 bg-white"
                    : "border-red-200 bg-white"
                }`}
              >
                {pkg.popular && (
                  <span className="absolute -top-2 right-3 rounded-full bg-red-600 px-2 py-0.5 text-[10px] font-semibold uppercase text-white">
                    Mais comprado
                  </span>
                )}
                <div className="text-base font-semibold text-ink">{pkg.label}</div>
                <div className="mt-1 text-2xl font-bold text-red-600">{pkg.price}</div>
                <div className="mt-2 text-xs text-slate-500">Pagamento via Pix/Boleto</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {!isBlocked && isLow && (
        <div className="rounded-[32px] border-2 border-amber-300 bg-amber-50 p-6">
          <div className="flex items-center gap-3">
            <div className="text-2xl">⚠️</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-amber-900">
                Suas mensagens estão acabando
              </h3>
              <p className="text-sm text-amber-700">
                Restam {remaining.toLocaleString("pt-BR")} de {total.toLocaleString("pt-BR")}. Considere comprar um pacote extra para não interromper o atendimento.
              </p>
            </div>
            <button
              onClick={() => alert("Em breve: integração ASAAS")}
              className="rounded-2xl bg-amber-600 px-5 py-2 text-sm font-semibold text-white hover:bg-amber-700"
            >
              Comprar mais
            </button>
          </div>
        </div>
      )}
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
    <Layout profile={profile} credits={credits}>
      <Routes>
        <Route path="/dashboard" element={<DashboardPage chats={chats} credits={credits} leads={leads} tasks={tasks} />} />
        <Route
          path="/chat"
          element={
            <ChatPage
              chats={chats}
              selectedChat={selectedChat}
              messages={messages}
              credits={credits}
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

