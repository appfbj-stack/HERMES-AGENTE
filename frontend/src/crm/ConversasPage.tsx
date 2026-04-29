import { FormEvent, useEffect, useState } from "react";
import {
  getCrmConversations,
  getCrmMessages,
  sendCrmConversationMessage,
  updateCrmConversationState,
} from "../api";

export default function ConversasPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [newMessage, setNewMessage] = useState("");

  async function loadConversations() {
    setLoading(true);
    setError("");
    try {
      const data = await getCrmConversations();
      setConversations(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar conversas");
    } finally {
      setLoading(false);
    }
  }

  async function loadMessages(conversationId: number) {
    setError("");
    try {
      const data = await getCrmMessages(conversationId);
      setMessages(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar mensagens");
    }
  }

  async function handleSendMessage(e: FormEvent) {
    e.preventDefault();
    if (!selectedConversation || !newMessage.trim()) return;

    setSending(true);
    setError("");
    try {
      const sentMessage = await sendCrmConversationMessage(selectedConversation.id, newMessage.trim());
      setMessages((prev) => [...prev, sentMessage]);
      setNewMessage("");
      
      // Atualizar última mensagem na conversa
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedConversation.id
            ? { ...c, last_message: newMessage.trim(), last_message_at: sentMessage.created_at }
            : c
        )
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao enviar mensagem");
    } finally {
      setSending(false);
    }
  }

  async function handleAssume() {
    if (!selectedConversation) return;

    try {
      const updated = await updateCrmConversationState(selectedConversation.id, {
        assigned_user_id: null, // Será preenchido pelo backend com o usuário atual
        ai_enabled: false,
        status: "open",
      });
      setSelectedConversation(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao assumir atendimento");
    }
  }

  async function handleReturnToAI() {
    if (!selectedConversation) return;

    try {
      const updated = await updateCrmConversationState(selectedConversation.id, {
        assigned_user_id: null,
        ai_enabled: true,
        status: "open",
      });
      setSelectedConversation(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao devolver para IA");
    }
  }

  async function handleResolve() {
    if (!selectedConversation) return;

    try {
      const updated = await updateCrmConversationState(selectedConversation.id, {
        status: "resolved",
      });
      setSelectedConversation(updated);
      setConversations((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao marcar como resolvido");
    }
  }

  function getChannelIcon(channel: string) {
    switch (channel) {
      case "whatsapp":
        return "📱";
      case "telegram":
        return "✈️";
      case "web":
        return "💬";
      default:
        return "📞";
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "open":
        return "bg-emerald-100 text-emerald-900";
      case "resolved":
        return "bg-blue-100 text-blue-900";
      case "closed":
        return "bg-slate-100 text-slate-900";
      default:
        return "bg-slate-100 text-slate-900";
    }
  }

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  return (
    <div className="h-[calc(100vh-140px)]">
      <div className="mb-6">
        <h1 className="text-3xl font-serif text-slate-900">Conversas</h1>
        <p className="text-slate-600">Gerencie todos os atendimentos do CRM</p>
      </div>

      {error && (
        <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Lista de Conversas */}
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-4 lg:col-span-1">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Atendimentos</h2>
            <span className="text-sm text-slate-500">{conversations.length} conversas</span>
          </div>

          {loading ? (
            <div className="py-8 text-center text-slate-500">Carregando...</div>
          ) : conversations.length === 0 ? (
            <div className="py-8 text-center text-slate-500">Nenhuma conversa ainda</div>
          ) : (
            <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv)}
                  className={`w-full rounded-2xl p-4 text-left transition ${
                    selectedConversation?.id === conv.id
                      ? "bg-brand text-white"
                      : "bg-slate-50 text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xl">{getChannelIcon(conv.channel)}</span>
                        <span className="font-semibold truncate">{conv.contact_name || "Sem nome"}</span>
                      </div>
                      {conv.contact_phone && (
                        <div className={`text-xs truncate ${selectedConversation?.id === conv.id ? "text-white/70" : "text-slate-500"}`}>
                          {conv.contact_phone}
                        </div>
                      )}
                      {conv.last_message && (
                        <div className={`mt-2 text-sm truncate ${selectedConversation?.id === conv.id ? "text-white/90" : "text-slate-600"}`}>
                          {conv.last_message}
                        </div>
                      )}
                    </div>
                    <div className="ml-2 flex flex-col items-end gap-1">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${selectedConversation?.id === conv.id ? "bg-white/20" : getStatusColor(conv.status)}`}>
                        {conv.status === "open" ? "Aberto" : conv.status === "resolved" ? "Resolvido" : "Fechado"}
                      </span>
                      {conv.last_message_at && (
                        <span className={`text-[10px] ${selectedConversation?.id === conv.id ? "text-white/60" : "text-slate-400"}`}>
                          {new Date(conv.last_message_at).toLocaleDateString("pt-BR")}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Chat */}
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-6 lg:col-span-2 flex flex-col">
          {selectedConversation ? (
            <>
              {/* Header */}
              <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getChannelIcon(selectedConversation.channel)}</span>
                  <div>
                    <h3 className="font-semibold text-slate-900">
                      {selectedConversation.contact_name || "Sem nome"}
                    </h3>
                    {selectedConversation.contact_phone && (
                      <p className="text-sm text-slate-500">{selectedConversation.contact_phone}</p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  {selectedConversation.assigned_user_id ? (
                    <button
                      onClick={handleReturnToAI}
                      className="rounded-xl bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                    >
                      Devolver para IA
                    </button>
                  ) : (
                    <button
                      onClick={handleAssume}
                      className="rounded-xl bg-brand px-3 py-2 text-xs font-semibold text-white hover:bg-brand/90"
                    >
                      Assumir Atendimento
                    </button>
                  )}
                  <button
                    onClick={handleResolve}
                    className="rounded-xl bg-emerald-100 px-3 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-200"
                  >
                    Resolver
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto mb-4 space-y-4 min-h-[400px] max-h-[calc(100vh-450px)]">
                {messages.length === 0 ? (
                  <div className="py-8 text-center text-slate-500">Nenhuma mensagem ainda</div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.sender_type === "assistant" ? "justify-start" : "justify-end"}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                          msg.sender_type === "assistant"
                            ? "bg-slate-100 text-slate-900"
                            : "bg-brand text-white"
                        }`}
                      >
                        <div className="text-sm">{msg.content}</div>
                        <div
                          className={`mt-1 text-[10px] ${
                            msg.sender_type === "assistant" ? "text-slate-400" : "text-white/70"
                          }`}
                        >
                          {new Date(msg.created_at).toLocaleString("pt-BR", {
                            dateStyle: "short",
                            timeStyle: "short",
                          })}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Input */}
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  className="flex-1 rounded-xl border-2 border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-brand"
                  disabled={sending}
                />
                <button
                  type="submit"
                  disabled={sending || !newMessage.trim()}
                  className="rounded-xl bg-brand px-6 py-3 font-semibold text-white hover:bg-brand/90 disabled:opacity-50"
                >
                  {sending ? "Enviando..." : "Enviar"}
                </button>
              </form>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500">
              <div className="text-center">
                <div className="text-6xl mb-4">💬</div>
                <p className="text-lg font-medium">Selecione uma conversa</p>
                <p className="text-sm">para começar o atendimento</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
