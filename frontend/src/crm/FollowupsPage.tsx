import { FormEvent, useEffect, useState } from "react";
import { createFollowup, deleteFollowup, getFollowups, getLeads, updateFollowup } from "../api";
import type { CrmFollowup, Lead } from "../types";

const STATUS_OPTS = ["pendente", "feito", "atrasado"];
const STATUS_LABEL: Record<string, string> = { pendente: "Pendente", feito: "Feito", atrasado: "Atrasado" };
const STATUS_COLOR: Record<string, string> = {
  pendente: "bg-amber-100 text-amber-700",
  feito: "bg-emerald-100 text-emerald-700",
  atrasado: "bg-red-100 text-red-700",
};
const CANAL_OPTS = ["whatsapp", "telegram", "ligacao", "presencial"];
const CANAL_ICON: Record<string, string> = {
  whatsapp: "📱", telegram: "✈️", ligacao: "📞", presencial: "🤝",
};

function toLocalDatetime(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatDatetime(iso: string | undefined) {
  if (!iso) return { date: "-", time: "-", isToday: false, isPast: false };
  const d = new Date(iso);
  const today = new Date();
  const isToday = d.toDateString() === today.toDateString();
  const isPast = d < today;
  const date = isToday
    ? "Hoje"
    : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
  const time = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return { date, time, isToday, isPast };
}

type FuForm = { lead_id: string; titulo: string; descricao: string; data_hora: string; canal: string };
const EMPTY: FuForm = {
  lead_id: "",
  titulo: "",
  descricao: "",
  data_hora: toLocalDatetime(new Date(Date.now() + 3600_000).toISOString()),
  canal: "whatsapp",
};

function FollowupModal({
  leads,
  onClose,
  onSaved,
}: {
  leads: Lead[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<FuForm>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createFollowup({
        lead_id: parseInt(form.lead_id, 10),
        title: form.titulo,
        description: form.descricao || undefined,
        due_at: form.data_hora,
        channel: form.canal,
      });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-[28px] bg-white p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-serif text-2xl">Novo Follow-up</h2>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">×</button>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Lead *</label>
            <select
              className="input mt-1"
              value={form.lead_id}
              onChange={(e) => setForm({ ...form, lead_id: e.target.value })}
              required
            >
              <option value="">Selecione um lead</option>
              {leads.map((l) => (
                <option key={l.id} value={l.id}>{l.name}{l.phone ? ` — ${l.phone}` : ""}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Título *</label>
            <input
              className="input mt-1"
              value={form.titulo}
              onChange={(e) => setForm({ ...form, titulo: e.target.value })}
              required
              placeholder="Ex: Ligar para confirmar proposta"
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Data e hora *</label>
              <input
                type="datetime-local"
                className="input mt-1"
                value={form.data_hora}
                onChange={(e) => setForm({ ...form, data_hora: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Canal</label>
              <select
                className="input mt-1"
                value={form.canal}
                onChange={(e) => setForm({ ...form, canal: e.target.value })}
              >
                {CANAL_OPTS.map((c) => (
                  <option key={c} value={c}>{CANAL_ICON[c]} {c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Descrição</label>
            <textarea
              className="input mt-1"
              rows={2}
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              placeholder="Detalhes do follow-up..."
            />
          </div>
          {error && <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="rounded-2xl bg-slate-100 px-5 py-2 text-sm hover:bg-slate-200">Cancelar</button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-2xl bg-violet-600 px-5 py-2.5 font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {saving ? "Salvando..." : "Criar follow-up"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function FollowupsPage() {
  const [followups, setFollowups] = useState<CrmFollowup[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [showModal, setShowModal] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [fuData, leadsData] = await Promise.all([
        getFollowups(filterStatus === "hoje" ? true : false),
        getLeads(),
      ]);
      setFollowups(fuData);
      setLeads(leadsData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus]);

  function leadName(id: number) {
    return leads.find((l) => l.id === id)?.name ?? `Lead #${id}`;
  }

  async function markDone(fu: CrmFollowup) {
    await updateFollowup(fu.id, { status: "feito" });
    setFollowups((prev) => prev.map((f) => (f.id === fu.id ? { ...f, status: "feito" } : f)));
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir este follow-up?")) return;
    await deleteFollowup(id);
    setFollowups((prev) => prev.filter((f) => f.id !== id));
  }

  // Agrupar: hoje, atrasados, futuros
  const now = new Date();
  const todayStr = now.toDateString();
  const groups = {
    atrasados: followups.filter((f) => f.status !== "feito" && new Date(f.data_hora || new Date().toISOString()) < now && new Date(f.data_hora || new Date().toISOString()).toDateString() !== todayStr),
    hoje: followups.filter((f) => new Date(f.data_hora || new Date().toISOString()).toDateString() === todayStr),
    futuros: followups.filter((f) => f.status !== "feito" && new Date(f.data_hora || new Date().toISOString()) > now && new Date(f.data_hora || new Date().toISOString()).toDateString() !== todayStr),
    feitos: followups.filter((f) => f.status === "feito"),
  };

  function GroupSection({ title, items, accent }: { title: string; items: CrmFollowup[]; accent?: string }) {
    if (items.length === 0) return null;
    return (
      <div>
        <div className={`mb-2 text-xs font-semibold uppercase tracking-wider ${accent ?? "text-slate-500"}`}>
          {title} ({items.length})
        </div>
        <div className="space-y-2">
          {items.map((fu) => {
            const { date, time, isPast } = formatDatetime(fu.data_hora);
            return (
              <div
                key={fu.id}
                className={`flex items-center gap-4 rounded-2xl border p-4 transition ${
                  fu.status === "feito"
                    ? "border-slate-100 bg-slate-50 opacity-60"
                    : isPast && fu.status !== "feito"
                    ? "border-red-200 bg-red-50"
                    : "border-slate-100 bg-white shadow-soft"
                }`}
              >
                <div className="flex h-10 w-10 shrink-0 flex-col items-center justify-center rounded-xl bg-violet-100 text-center">
                  <div className="text-[10px] font-bold uppercase text-violet-500">{date}</div>
                  <div className="text-xs font-semibold text-violet-700">{time}</div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-ink">{fu.titulo}</div>
                  <div className="text-xs text-slate-500">
                    {CANAL_ICON[fu.canal || "whatsapp"]} {fu.canal} · {leadName(fu.lead_id)}
                  </div>
                  {fu.descricao && <div className="mt-0.5 text-xs text-slate-400">{fu.descricao}</div>}
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_COLOR[fu.status] ?? ""}`}>
                    {STATUS_LABEL[fu.status]}
                  </span>
                  {fu.status !== "feito" && (
                    <button
                      onClick={() => markDone(fu)}
                      className="rounded-xl bg-emerald-100 px-2.5 py-1 text-xs text-emerald-700 hover:bg-emerald-200"
                      title="Marcar como feito"
                    >
                      ✓
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(fu.id)}
                    className="rounded-xl bg-slate-100 px-2 py-1 text-xs text-slate-500 hover:bg-red-100 hover:text-red-600"
                  >
                    ×
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl text-ink">Follow-ups</h1>
          <p className="mt-0.5 text-sm text-slate-500">{followups.length} agendado{followups.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="flex gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-soft outline-none"
          >
            <option value="">Todos</option>
            {STATUS_OPTS.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </select>
          <button
            onClick={() => setShowModal(true)}
            className="rounded-full bg-violet-600 px-5 py-2 text-sm font-semibold text-white hover:bg-violet-700"
          >
            + Follow-up
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400">Carregando...</div>
      ) : followups.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <div className="text-5xl">📅</div>
          <div className="text-base text-slate-500">Nenhum follow-up agendado</div>
          <button onClick={() => setShowModal(true)} className="rounded-full bg-violet-600 px-5 py-2 text-sm font-semibold text-white hover:bg-violet-700">
            Agendar agora
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <GroupSection title="⚠️ Atrasados" items={groups.atrasados} accent="text-red-600" />
          <GroupSection title="📅 Hoje" items={groups.hoje} accent="text-violet-600" />
          <GroupSection title="📆 Próximos" items={groups.futuros} />
          <GroupSection title="✅ Feitos" items={groups.feitos} />
        </div>
      )}

      {showModal && (
        <FollowupModal
          leads={leads}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); load(); }}
        />
      )}
    </div>
  );
}
