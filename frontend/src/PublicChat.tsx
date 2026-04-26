/**
 * Chat Público — página de atendimento estilo WhatsApp Web
 * URL: /c/:tenantId
 *
 * Sem login. Cliente final escaneia QR ou clica no link e cai aqui.
 * Sessão é guardada em localStorage pra continuar a conversa se voltar.
 */
import { FormEvent, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type PublicTenant = {
  id: number;
  name: string;
  niche: string | null;
  welcome: string;
  active: boolean;
};

type PublicMessage = {
  id: number;
  sender_type: "user" | "assistant" | "human";
  content: string;
  created_at: string;
};

function getOrCreateSessionId(tenantId: string): string {
  const key = `mac_session_${tenantId}`;
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

function getStoredName(tenantId: string): string {
  return localStorage.getItem(`mac_name_${tenantId}`) || "";
}

function setStoredName(tenantId: string, name: string) {
  localStorage.setItem(`mac_name_${tenantId}`, name);
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function getInitials(name: string): string {
  return (name || "?")
    .split(" ")
    .map((n) => n[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function PublicChat() {
  const { tenantId = "" } = useParams<{ tenantId: string }>();
  const sessionId = getOrCreateSessionId(tenantId);

  const [tenant, setTenant] = useState<PublicTenant | null>(null);
  const [messages, setMessages] = useState<PublicMessage[]>([]);
  const [input, setInput] = useState("");
  const [name, setName] = useState(getStoredName(tenantId));
  const [needsName, setNeedsName] = useState(!getStoredName(tenantId));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [blockedMsg, setBlockedMsg] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Carrega info do tenant
  useEffect(() => {
    fetch(`${API_BASE_URL}/public/tenant/${tenantId}`)
      .then((r) => {
        if (!r.ok) throw new Error("Tenant não encontrado");
        return r.json();
      })
      .then((data) => {
        setTenant(data);
        if (!data.active) {
          setError("Atendimento temporariamente indisponível.");
        }
      })
      .catch(() => setError("Empresa não encontrada. Verifique o link."));
  }, [tenantId]);

  // Carrega histórico
  useEffect(() => {
    if (!tenant) return;
    fetch(`${API_BASE_URL}/public/chat/${tenantId}/messages?session_id=${sessionId}`)
      .then((r) => r.json())
      .then((data: PublicMessage[]) => setMessages(data))
      .catch(() => {});
  }, [tenant, tenantId, sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    if (needsName) {
      if (!name.trim()) {
        alert("Digite seu nome pra começar.");
        return;
      }
      setStoredName(tenantId, name);
      setNeedsName(false);
    }

    const text = input;
    setInput("");
    setSending(true);
    setBlockedMsg("");

    // Otimismo: mostra a mensagem do cliente imediatamente
    const tempId = -Date.now();
    setMessages((m) => [
      ...m,
      {
        id: tempId,
        sender_type: "user",
        content: text,
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      const r = await fetch(`${API_BASE_URL}/public/chat/${tenantId}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          visitor_name: name || null,
          content: text,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao enviar");
      }
      const data = await r.json();
      // Substitui a mensagem temporária pela real
      setMessages((m) =>
        m
          .filter((msg) => msg.id !== tempId)
          .concat([data.user_message])
          .concat(data.assistant_message ? [data.assistant_message] : [])
      );
      if (data.blocked) {
        setBlockedMsg(data.blocked_reason || "");
      }
    } catch (e) {
      setMessages((m) => m.filter((msg) => msg.id !== tempId));
      setError(e instanceof Error ? e.message : "Erro ao enviar");
    } finally {
      setSending(false);
    }
  }

  if (error && !tenant) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#efeae2] p-6 text-center">
        <div className="rounded-2xl bg-white p-8 shadow-soft">
          <div className="text-4xl">😕</div>
          <p className="mt-3 text-slate-700">{error}</p>
        </div>
      </div>
    );
  }
  if (!tenant) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#efeae2]">
        <div className="text-slate-500">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-[#efeae2]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-black/5 bg-emerald-700 px-4 py-3 text-white">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-lg">
          💬
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold">Chat</div>
          <div className="text-xs text-white/80 flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-300" /> online
          </div>
        </div>
      </div>

      {/* Modal pedindo nome */}
      {needsName && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl">
            <div className="text-center text-3xl">👋</div>
            <h2 className="mt-2 text-center text-xl font-semibold">Olá!</h2>
            <p className="mt-2 text-center text-sm text-slate-600">
              Antes de começar, como você se chama?
            </p>
            <input
              autoFocus
              className="mt-4 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
              placeholder="Seu nome"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && name.trim()) {
                  setStoredName(tenantId, name);
                  setNeedsName(false);
                }
              }}
            />
            <button
              onClick={() => {
                if (name.trim()) {
                  setStoredName(tenantId, name);
                  setNeedsName(false);
                }
              }}
              className="mt-3 w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700"
            >
              Iniciar conversa
            </button>
          </div>
        </div>
      )}

      {/* Mensagens */}
      <div
        className="flex-1 overflow-y-auto px-3 py-4 md:px-6"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Cg fill='%23000' fill-opacity='0.025'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3z'/%3E%3C/g%3E%3C/svg%3E\")",
        }}
      >
        <div className="mx-auto max-w-3xl space-y-2">
          {messages.length === 0 && (
            <div className="mx-auto max-w-md rounded-2xl bg-white/80 px-5 py-3 text-center text-sm text-slate-600 shadow-sm">
              {tenant.welcome}
            </div>
          )}
          {messages.map((m) => {
            const mine = m.sender_type === "user";
            const isHuman = m.sender_type === "human";
            return (
              <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] whitespace-pre-wrap break-words px-3 py-2 text-sm shadow-sm md:max-w-[65%] ${
                    mine
                      ? "rounded-lg rounded-tr-none bg-[#d9fdd3] text-ink"
                      : isHuman
                        ? "rounded-lg rounded-tl-none bg-[#fff3c4] text-ink"
                        : "rounded-lg rounded-tl-none bg-white text-ink"
                  }`}
                >
                  <div>{m.content}</div>
                  <div className="mt-1 text-right text-[10px] text-slate-500">
                    {formatTime(m.created_at)}
                  </div>
                </div>
              </div>
            );
          })}
          {sending && (
            <div className="flex justify-start">
              <div className="rounded-lg rounded-tl-none bg-white px-4 py-2 text-sm text-slate-400 shadow-sm">
                <span className="inline-flex gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
                  <span
                    className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                    style={{ animationDelay: "0.15s" }}
                  />
                  <span
                    className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                    style={{ animationDelay: "0.3s" }}
                  />
                </span>
              </div>
            </div>
          )}
          {blockedMsg && (
            <div className="mx-auto max-w-md rounded-2xl bg-amber-50 px-4 py-3 text-center text-xs text-amber-800 shadow-sm">
              {blockedMsg}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <form
        onSubmit={send}
        className="flex items-center gap-2 border-t border-black/5 bg-[#f0f2f5] px-3 py-2.5"
      >
        <input
          className="flex-1 rounded-full bg-white px-4 py-2.5 text-sm outline-none ring-1 ring-black/5 focus:ring-emerald-500"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Digite uma mensagem"
          maxLength={800}
          disabled={sending || !tenant.active}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending || !tenant.active}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-600 text-white transition hover:bg-emerald-700 disabled:bg-slate-300"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </form>
    </div>
  );
}
