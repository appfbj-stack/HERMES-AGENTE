import { FormEvent, useEffect, useState } from "react";
import { createLead, deleteLead, getCrmTags, getLeads, updateLead } from "../api";
import type { CrmTag, Lead } from "../types";

const STATUS_OPTS = ["new", "contacted", "qualified", "proposal", "closed", "lost"];
const STATUS_LABEL: Record<string, string> = {
  new: "Novo",
  contacted: "Contactado",
  qualified: "Qualificado",
  proposal: "Proposta",
  closed: "Fechado",
  lost: "Perdido",
};
const STATUS_COLOR: Record<string, string> = {
  new: "bg-blue-100 text-blue-700",
  contacted: "bg-amber-100 text-amber-700",
  qualified: "bg-violet-100 text-violet-700",
  proposal: "bg-orange-100 text-orange-700",
  closed: "bg-emerald-100 text-emerald-700",
  lost: "bg-red-100 text-red-700",
};
const ORIGEM_OPTS = ["manual", "whatsapp", "telegram", "site"];
const ORIGEM_ICON: Record<string, string> = {
  manual: "✏️",
  whatsapp: "📱",
  telegram: "✈️",
  site: "🌐",
};

function Badge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${STATUS_COLOR[status] ?? "bg-slate-100 text-slate-600"}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

type LeadFormData = {
  name: string;
  phone: string;
  email: string;
  interesse: string;
  origem: string;
  status: string;
  observacoes: string;
};

const EMPTY_FORM: LeadFormData = {
  name: "",
  phone: "",
  email: "",
  interesse: "",
  origem: "manual",
  status: "new",
  observacoes: "",
};

function LeadModal({
  lead,
  tags,
  onClose,
  onSaved,
}: {
  lead?: Lead;
  tags: CrmTag[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<LeadFormData>(
    lead
      ? {
          name: lead.name,
          phone: lead.phone ?? "",
          email: lead.email ?? "",
          interesse: lead.interest ?? "",
          origem: lead.origem,
          status: lead.status,
          observacoes: lead.observacoes ?? "",
        }
      : EMPTY_FORM
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        name: form.name,
        phone: form.phone || null,
        email: form.email || null,
        interest: form.interesse || null,
        origem: form.origem,
        status: form.status,
        observacoes: form.observacoes || null,
      };
      if (lead) {
        await updateLead(lead.id, payload);
      } else {
        await createLead(payload);
      }
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-[28px] bg-white p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="font-serif text-2xl">{lead ? "Editar Lead" : "Novo Lead"}</h2>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">×</button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Nome *</label>
              <input
                className="input mt-1"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="Nome do lead"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Telefone</label>
              <input
                className="input mt-1"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+55 11 99999-9999"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Email</label>
              <input
                className="input mt-1"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="email@exemplo.com"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Origem</label>
              <select
                className="input mt-1"
                value={form.origem}
                onChange={(e) => setForm({ ...form, origem: e.target.value })}
              >
                {ORIGEM_OPTS.map((o) => (
                  <option key={o} value={o}>{ORIGEM_ICON[o]} {o.charAt(0).toUpperCase() + o.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Status</label>
              <select
                className="input mt-1"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                {STATUS_OPTS.map((s) => (
                  <option key={s} value={s}>{STATUS_LABEL[s]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Interesse</label>
              <input
                className="input mt-1"
                value={form.interesse}
                onChange={(e) => setForm({ ...form, interesse: e.target.value })}
                placeholder="Ex: Plano Pro, produto X..."
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Observações</label>
            <textarea
              className="input mt-1"
              rows={3}
              value={form.observacoes}
              onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
              placeholder="Anotações internas sobre o lead..."
            />
          </div>

          {error && <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="rounded-2xl bg-slate-100 px-5 py-2 text-sm hover:bg-slate-200">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-2xl bg-violet-600 px-5 py-2.5 font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {saving ? "Salvando..." : lead ? "Salvar alterações" : "Criar lead"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [tags, setTags] = useState<CrmTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterOrigem, setFilterOrigem] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editLead, setEditLead] = useState<Lead | undefined>();
  const [deleting, setDeleting] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [leadsData, tagsData] = await Promise.all([
        getLeads({ status: filterStatus || undefined, origem: filterOrigem || undefined, search: search || undefined }),
        getCrmTags(),
      ]);
      setLeads(leadsData);
      setTags(tagsData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus, filterOrigem]);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    load();
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir este lead? Esta ação não pode ser desfeita.")) return;
    setDeleting(id);
    try {
      await deleteLead(id);
      setLeads((prev) => prev.filter((l) => l.id !== id));
    } finally {
      setDeleting(null);
    }
  }

  function formatDate(iso: string | null) {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("pt-BR");
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl text-ink">Leads</h1>
          <p className="mt-0.5 text-sm text-slate-500">{leads.length} lead{leads.length !== 1 ? "s" : ""}</p>
        </div>
        <button
          onClick={() => { setEditLead(undefined); setShowModal(true); }}
          className="rounded-full bg-violet-600 px-5 py-2 text-sm font-semibold text-white hover:bg-violet-700"
        >
          + Novo lead
        </button>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-2">
        <form onSubmit={handleSearch} className="flex flex-1 items-center gap-2 rounded-2xl bg-white px-4 py-2 shadow-soft min-w-[220px]">
          <svg className="h-4 w-4 shrink-0 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
          </svg>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome, telefone ou email..."
            className="flex-1 bg-transparent text-sm outline-none"
          />
          <button type="submit" className="rounded-xl bg-violet-600 px-3 py-1 text-xs font-semibold text-white">Buscar</button>
        </form>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-soft outline-none"
        >
          <option value="">Todos os status</option>
          {STATUS_OPTS.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
        </select>

        <select
          value={filterOrigem}
          onChange={(e) => setFilterOrigem(e.target.value)}
          className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-soft outline-none"
        >
          <option value="">Todas as origens</option>
          {ORIGEM_OPTS.map((o) => <option key={o} value={o}>{ORIGEM_ICON[o]} {o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
        </select>

        {(filterStatus || filterOrigem || search) && (
          <button
            onClick={() => { setFilterStatus(""); setFilterOrigem(""); setSearch(""); load(); }}
            className="rounded-2xl bg-slate-100 px-3 py-2 text-xs text-slate-600 hover:bg-slate-200"
          >
            ✕ Limpar
          </button>
        )}
      </div>

      {/* Tabela */}
      <div className="overflow-hidden rounded-[24px] bg-white shadow-soft">
        {loading ? (
          <div className="py-16 text-center text-slate-400">Carregando...</div>
        ) : leads.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <div className="text-4xl">👥</div>
            <div className="mt-3 text-base">Nenhum lead encontrado</div>
            <div className="mt-1 text-sm">Clique em "Novo lead" para começar</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-100 text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3">Lead</th>
                  <th className="px-4 py-3">Contato</th>
                  <th className="px-4 py-3">Origem</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Interesse</th>
                  <th className="px-4 py-3">Criado em</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr key={lead.id} className="border-t border-slate-50 transition hover:bg-slate-50/70">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-violet-100 text-sm font-bold text-violet-700">
                          {lead.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-medium text-ink">{lead.name}</div>
                          {lead.email && <div className="text-xs text-slate-400">{lead.email}</div>}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{lead.phone ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className="text-base">{ORIGEM_ICON[lead.origem] ?? "—"}</span>
                      <span className="ml-1 text-xs capitalize text-slate-500">{lead.origem}</span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge status={lead.status} />
                    </td>
                    <td className="max-w-[160px] px-4 py-3">
                      <span className="truncate text-slate-500">{lead.interest ?? "—"}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">{formatDate(lead.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => { setEditLead(lead); setShowModal(true); }}
                          className="rounded-xl bg-slate-100 px-2.5 py-1 text-xs hover:bg-slate-200"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(lead.id)}
                          disabled={deleting === lead.id}
                          className="rounded-xl bg-red-50 px-2.5 py-1 text-xs text-red-600 hover:bg-red-100 disabled:opacity-50"
                        >
                          {deleting === lead.id ? "..." : "×"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <LeadModal
          lead={editLead}
          tags={tags}
          onClose={() => setShowModal(false)}
          onSaved={() => { setShowModal(false); load(); }}
        />
      )}
    </div>
  );
}
