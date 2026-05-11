import { useEffect, useState } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface PastoralMembro {
  id: number;
  tenant_id: number;
  nome: string;
  telefone: string | null;
  email: string | null;
  data_nascimento: string | null;
  endereco: string | null;
  data_batismo: string | null;
  cargo: string | null;
  ativo: boolean;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

interface PastoralCulto {
  id: number;
  tenant_id: number;
  tipo: string;
  data_culto: string;
  pregador: string | null;
  tema: string | null;
  presentes: number | null;
  visitantes: number | null;
  oferta: number | null;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

interface PastoralEvento {
  id: number;
  tenant_id: number;
  titulo: string;
  data_inicio: string;
  data_fim: string | null;
  local: string | null;
  descricao: string | null;
  responsavel: string | null;
  created_at: string;
  updated_at: string;
}

interface PastoralVisita {
  id: number;
  tenant_id: number;
  membro_id: number | null;
  nome_visitado: string | null;
  data_visita: string;
  local: string | null;
  feito_por: string | null;
  motivo: string | null;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

interface PastoralAconselhamento {
  id: number;
  tenant_id: number;
  membro_id: number | null;
  nome_aconselhado: string | null;
  data_sessao: string;
  assunto: string | null;
  feito_por: string | null;
  confidencial: boolean;
  observacoes: string | null;
  created_at: string;
  updated_at: string;
}

interface PastoralDashboard {
  total_membros: number;
  membros_ativos: number;
  cultos_mes: number;
  eventos_proximos: number;
  visitas_semana: number;
  aconselhamentos_mes: number;
}

// ─── API ─────────────────────────────────────────────────────────────────────

const BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

async function apiReq<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem("hermes_token");
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erro" }));
    throw new Error(err.detail || "Falha na requisição");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

const api = {
  dashboard: () => apiReq<PastoralDashboard>("/agenda-pastoral/dashboard"),
  membros: () => apiReq<PastoralMembro[]>("/agenda-pastoral/membros"),
  createMembro: (d: object) => apiReq<PastoralMembro>("/agenda-pastoral/membros", { method: "POST", body: JSON.stringify(d) }),
  updateMembro: (id: number, d: object) => apiReq<PastoralMembro>(`/agenda-pastoral/membros/${id}`, { method: "PUT", body: JSON.stringify(d) }),
  deleteMembro: (id: number) => apiReq<void>(`/agenda-pastoral/membros/${id}`, { method: "DELETE" }),
  cultos: () => apiReq<PastoralCulto[]>("/agenda-pastoral/cultos"),
  createCulto: (d: object) => apiReq<PastoralCulto>("/agenda-pastoral/cultos", { method: "POST", body: JSON.stringify(d) }),
  deleteCulto: (id: number) => apiReq<void>(`/agenda-pastoral/cultos/${id}`, { method: "DELETE" }),
  eventos: () => apiReq<PastoralEvento[]>("/agenda-pastoral/eventos"),
  createEvento: (d: object) => apiReq<PastoralEvento>("/agenda-pastoral/eventos", { method: "POST", body: JSON.stringify(d) }),
  deleteEvento: (id: number) => apiReq<void>(`/agenda-pastoral/eventos/${id}`, { method: "DELETE" }),
  visitas: () => apiReq<PastoralVisita[]>("/agenda-pastoral/visitas"),
  createVisita: (d: object) => apiReq<PastoralVisita>("/agenda-pastoral/visitas", { method: "POST", body: JSON.stringify(d) }),
  deleteVisita: (id: number) => apiReq<void>(`/agenda-pastoral/visitas/${id}`, { method: "DELETE" }),
  aconselhamentos: () => apiReq<PastoralAconselhamento[]>("/agenda-pastoral/aconselhamentos"),
  createAconselhamento: (d: object) => apiReq<PastoralAconselhamento>("/agenda-pastoral/aconselhamentos", { method: "POST", body: JSON.stringify(d) }),
  deleteAconselhamento: (id: number) => apiReq<void>(`/agenda-pastoral/aconselhamentos/${id}`, { method: "DELETE" }),
};

// ─── UI Primitives ────────────────────────────────────────────────────────────

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`bg-slate-800/60 border border-white/8 rounded-2xl p-4 ${className}`}>{children}</div>;
}

function Btn({ children, type = "button", onClick, disabled, variant = "primary", className = "" }: {
  children: React.ReactNode; type?: "button" | "submit"; onClick?: () => void; disabled?: boolean; variant?: "primary" | "ghost" | "danger"; className?: string;
}) {
  const base = "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition-all disabled:opacity-50 cursor-pointer";
  const variants = { primary: "bg-green-600 hover:bg-green-500 text-white", ghost: "bg-white/8 hover:bg-white/15 text-slate-300", danger: "bg-red-500/20 hover:bg-red-500/40 text-red-300" };
  return <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]} ${className}`}>{children}</button>;
}

function Input({ label, value, onChange, type = "text", required, placeholder }: {
  label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; type?: string; required?: boolean; placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</label>
      <input type={type} value={value} onChange={onChange} required={required} placeholder={placeholder}
        className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-green-500/60 transition-colors" />
    </div>
  );
}

function Textarea({ label, value, onChange }: { label: string; value: string; onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</label>
      <textarea value={value} onChange={onChange} rows={3}
        className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-green-500/60 transition-colors resize-none" />
    </div>
  );
}

function StatCard({ icon, label, value, sub }: { icon: string; label: string; value: number; sub?: string }) {
  return (
    <Card className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-2xl bg-green-500/15 flex items-center justify-center text-2xl shrink-0">{icon}</div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-slate-400">{label}</p>
        {sub && <p className="text-xs text-slate-500">{sub}</p>}
      </div>
    </Card>
  );
}

function fmtDate(val?: string | null) {
  if (!val) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(val));
}

function fmtDateTime(val?: string | null) {
  if (!val) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(val));
}

// ─── Dashboard Tab ────────────────────────────────────────────────────────────

function DashboardTab() {
  const [data, setData] = useState<PastoralDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.dashboard().then(setData).finally(() => setLoading(false)); }, []);
  if (loading) return <p className="text-slate-400 text-sm">Carregando…</p>;
  if (!data) return <p className="text-slate-500 text-sm">Erro ao carregar dashboard.</p>;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard icon="👥" label="Total de membros" value={data.total_membros} />
        <StatCard icon="✅" label="Membros ativos" value={data.membros_ativos} />
        <StatCard icon="⛪" label="Cultos este mês" value={data.cultos_mes} />
        <StatCard icon="📅" label="Eventos próximos" value={data.eventos_proximos} />
        <StatCard icon="🏠" label="Visitas esta semana" value={data.visitas_semana} />
        <StatCard icon="💬" label="Aconselhamentos no mês" value={data.aconselhamentos_mes} />
      </div>
    </div>
  );
}

// ─── Membros Tab ──────────────────────────────────────────────────────────────

function MembrosTab() {
  const [membros, setMembros] = useState<PastoralMembro[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome: "", telefone: "", email: "", cargo: "", ativo: true, observacoes: "" });
  const [saving, setSaving] = useState(false);
  const load = () => { setLoading(true); api.membros().then(setMembros).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.createMembro({ ...form, telefone: form.telefone || null, email: form.email || null, cargo: form.cargo || null, observacoes: form.observacoes || null });
      setShowForm(false); setForm({ nome: "", telefone: "", email: "", cargo: "", ativo: true, observacoes: "" }); load();
    } catch (err) { alert(err instanceof Error ? err.message : "Erro"); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-sm text-slate-400">{membros.filter(m => m.ativo).length} ativos · {membros.filter(m => !m.ativo).length} inativos</p>
        <Btn onClick={() => setShowForm(!showForm)}>+ Novo Membro</Btn>
      </div>
      {showForm && (
        <Card>
          <p className="text-sm font-bold text-green-400 mb-4">Novo Membro</p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input label="Nome *" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required />
            <Input label="Telefone" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: e.target.value }))} />
            <Input label="E-mail" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            <Input label="Cargo" value={form.cargo} onChange={e => setForm(f => ({ ...f, cargo: e.target.value }))} />
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Ativo?</label>
              <input type="checkbox" checked={form.ativo} onChange={e => setForm(f => ({ ...f, ativo: e.target.checked }))} className="w-4 h-4" />
            </div>
            <div className="md:col-span-2"><Textarea label="Observações" value={form.observacoes} onChange={e => setForm(f => ({ ...f, observacoes: e.target.value }))} /></div>
            <div className="md:col-span-2 flex gap-2">
              <Btn type="submit" disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Btn>
              <Btn type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Btn>
            </div>
          </form>
        </Card>
      )}
      {loading ? <p className="text-slate-400 text-sm">Carregando…</p> : membros.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">Nenhum membro cadastrado.</p>
      ) : (
        <div className="space-y-2">
          {membros.map(m => (
            <Card key={m.id} className="flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-white font-medium">{m.nome}</p>
                  {m.cargo && <span className="text-xs bg-green-500/20 text-green-300 rounded-full px-2 py-0.5">{m.cargo}</span>}
                  {!m.ativo && <span className="text-xs bg-slate-700 text-slate-400 rounded-full px-2 py-0.5">Inativo</span>}
                </div>
                <p className="text-slate-400 text-xs mt-0.5">{[m.telefone, m.email].filter(Boolean).join(" · ") || "Sem contato"}</p>
              </div>
              <Btn variant="danger" onClick={async () => { if (confirm("Remover membro?")) { await api.deleteMembro(m.id); load(); } }} className="shrink-0 text-xs py-1 px-2">✕</Btn>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Cultos Tab ───────────────────────────────────────────────────────────────

function CultosTab() {
  const [cultos, setCultos] = useState<PastoralCulto[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ tipo: "Culto Dominical", data_culto: "", pregador: "", tema: "", presentes: "", visitantes: "", oferta: "" });
  const [saving, setSaving] = useState(false);
  const load = () => { setLoading(true); api.cultos().then(setCultos).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.createCulto({ tipo: form.tipo, data_culto: form.data_culto, pregador: form.pregador || null, tema: form.tema || null, presentes: form.presentes ? parseInt(form.presentes) : null, visitantes: form.visitantes ? parseInt(form.visitantes) : null, oferta: form.oferta ? parseFloat(form.oferta) : null });
      setShowForm(false); setForm({ tipo: "Culto Dominical", data_culto: "", pregador: "", tema: "", presentes: "", visitantes: "", oferta: "" }); load();
    } catch (err) { alert(err instanceof Error ? err.message : "Erro"); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Btn onClick={() => setShowForm(!showForm)}>+ Novo Culto</Btn></div>
      {showForm && (
        <Card>
          <p className="text-sm font-bold text-green-400 mb-4">Registrar Culto</p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Tipo *</label>
              <select value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))} className="bg-slate-900/60 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500/60">
                {["Culto Dominical", "Culto de Oração", "Culto de Jovens", "Culto de Família", "Culto Especial"].map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <Input label="Data *" type="datetime-local" value={form.data_culto} onChange={e => setForm(f => ({ ...f, data_culto: e.target.value }))} required />
            <Input label="Pregador" value={form.pregador} onChange={e => setForm(f => ({ ...f, pregador: e.target.value }))} />
            <Input label="Tema" value={form.tema} onChange={e => setForm(f => ({ ...f, tema: e.target.value }))} />
            <Input label="Presentes" type="number" value={form.presentes} onChange={e => setForm(f => ({ ...f, presentes: e.target.value }))} />
            <Input label="Visitantes" type="number" value={form.visitantes} onChange={e => setForm(f => ({ ...f, visitantes: e.target.value }))} />
            <Input label="Oferta (R$)" type="number" value={form.oferta} onChange={e => setForm(f => ({ ...f, oferta: e.target.value }))} placeholder="0.00" />
            <div className="md:col-span-2 flex gap-2">
              <Btn type="submit" disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Btn>
              <Btn type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Btn>
            </div>
          </form>
        </Card>
      )}
      {loading ? <p className="text-slate-400 text-sm">Carregando…</p> : cultos.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">Nenhum culto registrado.</p>
      ) : (
        <div className="space-y-3">
          {cultos.map(c => (
            <Card key={c.id} className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-white font-medium">⛪ {c.tipo}</p>
                  <span className="text-xs text-slate-400">{fmtDateTime(c.data_culto)}</span>
                </div>
                {c.pregador && <p className="text-slate-300 text-sm mt-1">👤 {c.pregador}{c.tema ? ` — ${c.tema}` : ""}</p>}
                <div className="flex gap-3 mt-1 flex-wrap">
                  {c.presentes != null && <span className="text-xs text-slate-400">👥 {c.presentes} presentes</span>}
                  {c.visitantes != null && <span className="text-xs text-slate-400">🙋 {c.visitantes} visitantes</span>}
                  {c.oferta != null && <span className="text-xs text-slate-400">💰 R$ {c.oferta.toFixed(2)}</span>}
                </div>
              </div>
              <Btn variant="danger" onClick={async () => { if (confirm("Remover culto?")) { await api.deleteCulto(c.id); load(); } }} className="shrink-0 text-xs py-1 px-2">✕</Btn>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Eventos Tab ──────────────────────────────────────────────────────────────

function EventosTab() {
  const [eventos, setEventos] = useState<PastoralEvento[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ titulo: "", data_inicio: "", data_fim: "", local: "", responsavel: "", descricao: "" });
  const [saving, setSaving] = useState(false);
  const load = () => { setLoading(true); api.eventos().then(setEventos).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.createEvento({ titulo: form.titulo, data_inicio: form.data_inicio, data_fim: form.data_fim || null, local: form.local || null, responsavel: form.responsavel || null, descricao: form.descricao || null });
      setShowForm(false); setForm({ titulo: "", data_inicio: "", data_fim: "", local: "", responsavel: "", descricao: "" }); load();
    } catch (err) { alert(err instanceof Error ? err.message : "Erro"); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Btn onClick={() => setShowForm(!showForm)}>+ Novo Evento</Btn></div>
      {showForm && (
        <Card>
          <p className="text-sm font-bold text-green-400 mb-4">Criar Evento</p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="md:col-span-2"><Input label="Título *" value={form.titulo} onChange={e => setForm(f => ({ ...f, titulo: e.target.value }))} required /></div>
            <Input label="Início *" type="datetime-local" value={form.data_inicio} onChange={e => setForm(f => ({ ...f, data_inicio: e.target.value }))} required />
            <Input label="Fim" type="datetime-local" value={form.data_fim} onChange={e => setForm(f => ({ ...f, data_fim: e.target.value }))} />
            <Input label="Local" value={form.local} onChange={e => setForm(f => ({ ...f, local: e.target.value }))} />
            <Input label="Responsável" value={form.responsavel} onChange={e => setForm(f => ({ ...f, responsavel: e.target.value }))} />
            <div className="md:col-span-2"><Textarea label="Descrição" value={form.descricao} onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))} /></div>
            <div className="md:col-span-2 flex gap-2">
              <Btn type="submit" disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Btn>
              <Btn type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Btn>
            </div>
          </form>
        </Card>
      )}
      {loading ? <p className="text-slate-400 text-sm">Carregando…</p> : eventos.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">Nenhum evento registrado.</p>
      ) : (
        <div className="space-y-3">
          {eventos.map(ev => (
            <Card key={ev.id} className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="text-white font-medium">📅 {ev.titulo}</p>
                <p className="text-slate-400 text-sm">{fmtDateTime(ev.data_inicio)}{ev.data_fim ? ` → ${fmtDateTime(ev.data_fim)}` : ""}</p>
                {ev.local && <p className="text-slate-400 text-xs">📍 {ev.local}</p>}
                {ev.responsavel && <p className="text-slate-400 text-xs">👤 {ev.responsavel}</p>}
                {ev.descricao && <p className="text-slate-300 text-sm mt-1">{ev.descricao}</p>}
              </div>
              <Btn variant="danger" onClick={async () => { if (confirm("Remover evento?")) { await api.deleteEvento(ev.id); load(); } }} className="shrink-0 text-xs py-1 px-2">✕</Btn>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Visitas Tab ──────────────────────────────────────────────────────────────

function VisitasTab() {
  const [visitas, setVisitas] = useState<PastoralVisita[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome_visitado: "", data_visita: "", local: "", feito_por: "", motivo: "", observacoes: "" });
  const [saving, setSaving] = useState(false);
  const load = () => { setLoading(true); api.visitas().then(setVisitas).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.createVisita({ nome_visitado: form.nome_visitado || null, data_visita: form.data_visita, local: form.local || null, feito_por: form.feito_por || null, motivo: form.motivo || null, observacoes: form.observacoes || null });
      setShowForm(false); setForm({ nome_visitado: "", data_visita: "", local: "", feito_por: "", motivo: "", observacoes: "" }); load();
    } catch (err) { alert(err instanceof Error ? err.message : "Erro"); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Btn onClick={() => setShowForm(!showForm)}>+ Nova Visita</Btn></div>
      {showForm && (
        <Card>
          <p className="text-sm font-bold text-green-400 mb-4">Registrar Visita</p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input label="Nome do visitado" value={form.nome_visitado} onChange={e => setForm(f => ({ ...f, nome_visitado: e.target.value }))} />
            <Input label="Data da Visita *" type="datetime-local" value={form.data_visita} onChange={e => setForm(f => ({ ...f, data_visita: e.target.value }))} required />
            <Input label="Local" value={form.local} onChange={e => setForm(f => ({ ...f, local: e.target.value }))} />
            <Input label="Feito por" value={form.feito_por} onChange={e => setForm(f => ({ ...f, feito_por: e.target.value }))} />
            <div className="md:col-span-2"><Textarea label="Motivo" value={form.motivo} onChange={e => setForm(f => ({ ...f, motivo: e.target.value }))} /></div>
            <div className="md:col-span-2"><Textarea label="Observações" value={form.observacoes} onChange={e => setForm(f => ({ ...f, observacoes: e.target.value }))} /></div>
            <div className="md:col-span-2 flex gap-2">
              <Btn type="submit" disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Btn>
              <Btn type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Btn>
            </div>
          </form>
        </Card>
      )}
      {loading ? <p className="text-slate-400 text-sm">Carregando…</p> : visitas.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">Nenhuma visita registrada.</p>
      ) : (
        <div className="space-y-3">
          {visitas.map(v => (
            <Card key={v.id} className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="text-white font-medium">{v.nome_visitado ?? `Membro #${v.membro_id}`}</p>
                <p className="text-slate-400 text-sm">🏠 {fmtDateTime(v.data_visita)}{v.local ? ` — 📍 ${v.local}` : ""}</p>
                {v.feito_por && <p className="text-slate-400 text-xs">👤 {v.feito_por}</p>}
                {v.motivo && <p className="text-slate-300 text-sm mt-1">{v.motivo}</p>}
              </div>
              <Btn variant="danger" onClick={async () => { if (confirm("Remover visita?")) { await api.deleteVisita(v.id); load(); } }} className="shrink-0 text-xs py-1 px-2">✕</Btn>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Aconselhamentos Tab ──────────────────────────────────────────────────────

function AconselhamentosTab() {
  const [items, setItems] = useState<PastoralAconselhamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome_aconselhado: "", data_sessao: "", assunto: "", feito_por: "", confidencial: true, observacoes: "" });
  const [saving, setSaving] = useState(false);
  const load = () => { setLoading(true); api.aconselhamentos().then(setItems).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.createAconselhamento({ nome_aconselhado: form.nome_aconselhado || null, data_sessao: form.data_sessao, assunto: form.assunto || null, feito_por: form.feito_por || null, confidencial: form.confidencial, observacoes: form.confidencial ? null : (form.observacoes || null) });
      setShowForm(false); setForm({ nome_aconselhado: "", data_sessao: "", assunto: "", feito_por: "", confidencial: true, observacoes: "" }); load();
    } catch (err) { alert(err instanceof Error ? err.message : "Erro"); } finally { setSaving(false); }
  };
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <p className="text-xs text-slate-400">🔒 Registros confidenciais ficam com observações ocultas.</p>
        <Btn onClick={() => setShowForm(!showForm)}>+ Novo Aconselhamento</Btn>
      </div>
      {showForm && (
        <Card>
          <p className="text-sm font-bold text-purple-400 mb-4">Registrar Aconselhamento</p>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input label="Nome do aconselhado" value={form.nome_aconselhado} onChange={e => setForm(f => ({ ...f, nome_aconselhado: e.target.value }))} />
            <Input label="Data da Sessão *" type="datetime-local" value={form.data_sessao} onChange={e => setForm(f => ({ ...f, data_sessao: e.target.value }))} required />
            <Input label="Assunto" value={form.assunto} onChange={e => setForm(f => ({ ...f, assunto: e.target.value }))} />
            <Input label="Feito por" value={form.feito_por} onChange={e => setForm(f => ({ ...f, feito_por: e.target.value }))} />
            <div className="flex items-center gap-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Confidencial?</label>
              <input type="checkbox" checked={form.confidencial} onChange={e => setForm(f => ({ ...f, confidencial: e.target.checked }))} className="w-4 h-4" />
            </div>
            {!form.confidencial && <div className="md:col-span-2"><Textarea label="Observações" value={form.observacoes} onChange={e => setForm(f => ({ ...f, observacoes: e.target.value }))} /></div>}
            <div className="md:col-span-2 flex gap-2">
              <Btn type="submit" disabled={saving}>{saving ? "Salvando…" : "Salvar"}</Btn>
              <Btn type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Btn>
            </div>
          </form>
        </Card>
      )}
      {loading ? <p className="text-slate-400 text-sm">Carregando…</p> : items.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">Nenhum aconselhamento registrado.</p>
      ) : (
        <div className="space-y-3">
          {items.map(a => (
            <Card key={a.id} className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-white font-medium">{a.nome_aconselhado ?? "—"}</span>
                  {a.confidencial && <span className="text-xs bg-purple-500/20 text-purple-300 rounded-full px-2 py-0.5">🔒 Confidencial</span>}
                </div>
                <p className="text-slate-400 text-sm">📅 {fmtDateTime(a.data_sessao)}</p>
                {a.assunto && <p className="text-slate-300 text-sm mt-1">📋 {a.assunto}</p>}
                {a.feito_por && <p className="text-slate-400 text-xs">👤 {a.feito_por}</p>}
                {!a.confidencial && a.observacoes && <p className="text-slate-400 text-sm mt-1">{a.observacoes}</p>}
              </div>
              <Btn variant="danger" onClick={async () => { if (confirm("Remover aconselhamento?")) { await api.deleteAconselhamento(a.id); load(); } }} className="shrink-0 text-xs py-1 px-2">✕</Btn>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Workspace ───────────────────────────────────────────────────────────

type Tab = "dashboard" | "membros" | "cultos" | "eventos" | "visitas" | "aconselhamentos";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "dashboard", label: "Dashboard", icon: "🏠" },
  { key: "membros", label: "Membros", icon: "👥" },
  { key: "cultos", label: "Cultos", icon: "⛪" },
  { key: "eventos", label: "Eventos", icon: "📅" },
  { key: "visitas", label: "Visitas", icon: "🏘️" },
  { key: "aconselhamentos", label: "Aconselhamento", icon: "💬" },
];

export default function PastoralWorkspace() {
  const [tab, setTab] = useState<Tab>("dashboard");
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="bg-gradient-to-r from-green-900/40 via-slate-900 to-purple-900/40 border-b border-white/8 px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-green-500 to-purple-600 flex items-center justify-center text-xl">⛪</div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Agenda Pastoral</h1>
            <p className="text-xs text-slate-400">Gestão pastoral da sua igreja</p>
          </div>
        </div>
      </div>
      <div className="flex gap-1 overflow-x-auto px-6 pt-4 pb-0 border-b border-white/8">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 whitespace-nowrap px-4 py-2.5 text-sm font-medium rounded-t-xl transition-all border-b-2 -mb-px ${tab === t.key ? "text-green-400 border-green-400 bg-green-400/5" : "text-slate-400 border-transparent hover:text-white hover:bg-white/5"}`}>
            <span>{t.icon}</span><span>{t.label}</span>
          </button>
        ))}
      </div>
      <div className="px-6 py-6">
        {tab === "dashboard" && <DashboardTab />}
        {tab === "membros" && <MembrosTab />}
        {tab === "cultos" && <CultosTab />}
        {tab === "eventos" && <EventosTab />}
        {tab === "visitas" && <VisitasTab />}
        {tab === "aconselhamentos" && <AconselhamentosTab />}
      </div>
    </div>
  );
}
