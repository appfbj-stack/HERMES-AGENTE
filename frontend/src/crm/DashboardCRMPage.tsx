import { useEffect, useState } from "react";
import {
  getCrmDashboard,
} from "../api";

export default function DashboardCRMPage() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const data = await getCrmDashboard();
      setDashboard(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  function getMetricColor(label: string): string {
    switch (label) {
      case "Leads":
      case "Atendimentos":
      case "Fechados":
        return "bg-emerald-50 text-emerald-900";
      case "Novos Leads":
      case "Ativas":
        return "bg-violet-50 text-violet-900";
      case "Follow-ups Hoje":
        return "bg-amber-50 text-amber-900";
      default:
        return "bg-slate-50 text-slate-900";
    }
  }

  const metrics = dashboard
    ? [
        { label: "Leads", value: dashboard.total_leads, icon: "👥" },
        { label: "Novos Leads", value: dashboard.new_leads, icon: "✨" },
        { label: "Atendimentos", value: dashboard.open_conversations, icon: "💬" },
        { label: "Follow-ups Hoje", value: dashboard.today_followups, icon: "📅" },
        { label: "Ativas", value: dashboard.active_conversations, icon: "⚡" },
        { label: "Fechados", value: dashboard.closed_won, icon: "✅" },
        { label: "Mensagens", value: dashboard.messages_used_month, icon: "📊" },
        { label: "Plano", value: dashboard.current_plan, icon: "💎" },
      ]
    : [];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-serif text-slate-900">Dashboard CRM</h1>
        <p className="text-slate-600">Visão geral do seu CRM</p>
      </div>

      {error && (
        <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-8 text-center text-slate-500">
          Carregando dashboard...
        </div>
      ) : dashboard ? (
        <div className="space-y-6">
          {/* Métricas */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric) => (
              <div
                key={metric.label}
                className={`rounded-[32px] p-6 shadow-soft backdrop-blur ${getMetricColor(metric.label)}`}
              >
                <div className="text-xs uppercase tracking-wider opacity-70 mb-2">{metric.label}</div>
                <div className="flex items-center justify-between">
                  <div className="text-4xl font-bold">{metric.value}</div>
                  <div className="text-4xl">{metric.icon}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Resumo */}
          <div className="rounded-[32px] border-2 border-slate-200 bg-white p-6 shadow-soft">
            <h2 className="text-xl font-serif font-semibold text-slate-900 mb-4">Resumo do Período</h2>
            <div className="grid gap-6 md:grid-cols-3">
              <div className="space-y-2">
                <div className="text-sm text-slate-500">Performance de Leads</div>
                <div className="text-2xl font-bold text-slate-900">
                  {dashboard.total_leads > 0
                    ? Math.round((dashboard.closed_won / dashboard.total_leads) * 100)
                    : 0}
                  %
                </div>
                <div className="text-xs text-slate-400">Taxa de conversão</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-slate-500">Atendimentos Ativos</div>
                <div className="text-2xl font-bold text-slate-900">{dashboard.active_conversations}</div>
                <div className="text-xs text-slate-400">Conversas em andamento</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-slate-500">Plano Atual</div>
                <div className="text-2xl font-bold text-brand capitalize">
                  {dashboard.current_plan}
                </div>
                <div className="text-xs text-slate-400">
                  {dashboard.messages_used_month.toLocaleString("pt-BR")} mensagens usadas
                </div>
              </div>
            </div>
          </div>

          {/* Ações Rápidas */}
          <div className="rounded-[32px] border-2 border-slate-200 bg-white p-6 shadow-soft">
            <h2 className="text-xl font-serif font-semibold text-slate-900 mb-4">Ações Rápidas</h2>
            <div className="grid gap-3 md:grid-cols-3">
              <a
                href="/crm/leads"
                className="rounded-2xl bg-slate-50 p-4 text-center hover:bg-slate-100 transition"
              >
                <div className="text-3xl mb-2">👥</div>
                <div className="font-semibold text-slate-900">Ver Leads</div>
                <div className="text-xs text-slate-500">Gerenciar seus leads</div>
              </a>
              <a
                href="/crm/kanban"
                className="rounded-2xl bg-slate-50 p-4 text-center hover:bg-slate-100 transition"
              >
                <div className="text-3xl mb-2">📋</div>
                <div className="font-semibold text-slate-900">Ver Kanban</div>
                <div className="text-xs text-slate-500">Gerenciar pipeline</div>
              </a>
              <a
                href="/crm/followups"
                className="rounded-2xl bg-slate-50 p-4 text-center hover:bg-slate-100 transition"
              >
                <div className="text-3xl mb-2">📅</div>
                <div className="font-semibold text-slate-900">Ver Follow-ups</div>
                <div className="text-xs text-slate-500">{dashboard.today_followups} para hoje</div>
              </a>
            </div>
          </div>

          {/* Alertas */}
          {dashboard.today_followups > 0 && (
            <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-4">
              <div className="flex items-center gap-3">
                <div className="text-2xl">⚠️</div>
                <div>
                  <div className="font-semibold text-amber-900">Follow-ups Pendentes</div>
                  <div className="text-sm text-amber-800">
                    Você tem {dashboard.today_followups} follow-up(s) agendado(s) para hoje.
                  </div>
                </div>
                <a
                  href="/crm/followups"
                  className="ml-auto rounded-full bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
                >
                  Ver Todos
                </a>
              </div>
            </div>
          )}

          {dashboard.open_conversations > 0 && (
            <div className="rounded-2xl border-2 border-violet-300 bg-violet-50 p-4">
              <div className="flex items-center gap-3">
                <div className="text-2xl">💬</div>
                <div>
                  <div className="font-semibold text-violet-900">Atendimentos em Aberto</div>
                  <div className="text-sm text-violet-800">
                    {dashboard.open_conversations} conversa(s) aguardando resposta.
                  </div>
                </div>
                <a
                  href="/crm/conversations"
                  className="ml-auto rounded-full bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700"
                >
                  Ver Todos
                </a>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
