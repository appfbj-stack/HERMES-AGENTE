import { FormEvent, useEffect, useState } from "react";
import {
  getCrmLeads,
  createCrmLead,
  updateCrmLead,
  deleteCrmLead,
  getCrmTags,
} from "../api";

type CrmLead = any;
type CrmTag = any;

export default function LeadsPage() {
  const [leads, setLeads] = useState<CrmLead[]>([]);
  const [tags, setTags] = useState<CrmTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedLead, setSelectedLead] = useState<CrmLead | null>(null);
  const [saved, setSaved] = useState(false);

  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    origem: "manual",
    status: "Novo lead",
    observacoes: "",
    interesse: "",
  });

  // TODO: fix ORIGEM_ICON initialization issue
  // const ORIGEM_ICON = {
  //   manual: "📝",
  //   whatsapp: "📱",
  //   telegram: "✈️",
  //   site: "🌐",
  // };

  async function load() {
    setLoading(true);
    try {
      const [leadsData, tagsData] = await Promise.all([
        getCrmLeads(),
        getCrmTags(),
      ]);
      setLeads(leadsData);
      setTags(tagsData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save(e: FormEvent) {
    e.preventDefault();
    setSaved(false);

    try {
      if (selectedLead) {
        await updateCrmLead(selectedLead.id, form);
      } else {
        await createCrmLead(form);
      }
      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        setShowModal(false);
        setSelectedLead(null);
        load();
      }, 1000);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Tem certeza que deseja excluir este lead?")) return;
    try {
      await deleteCrmLead(id);
      load();
    } catch (e) {
      console.error(e);
    }
  }

  function getStatusColor(status: string) {
    switch (status.toLowerCase()) {
      case "novo lead":
        return "bg-violet-100 text-violet-900";
      case "em atendimento":
        return "bg-blue-100 text-blue-900";
      case "fechado":
        return "bg-emerald-100 text-emerald-900";
      case "perdido":
        return "bg-red-100 text-red-900";
      default:
        return "bg-slate-100 text-slate-900";
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif text-slate-900">Leads</h1>
          <p className="text-slate-600">Gerencie seus leads</p>
        </div>
        <button
          onClick={() => {
            setForm({
              name: "",
              phone: "",
              email: "",
              origem: "manual",
              status: "Novo lead",
              observacoes: "",
              interesse: "",
            });
            setSelectedLead(null);
            setShowModal(true);
          }}
          className="rounded-full bg-brand px-6 py-3 text-sm font-semibold text-white hover:bg-brand/90"
        >
          + Novo Lead
        </button>
      </div>

      {loading ? (
        <div className="rounded-3xl border-2 border-slate-200 bg-white p-8 text-center text-slate-500">
          Carregando...
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {leads.map((lead) => (
            <div
              key={lead.id}
              onClick={() => {
                setSelectedLead(lead);
                setForm({
                  name: lead.name,
                  phone: lead.phone || "",
                  email: lead.email || "",
                  origem: lead.origem || "manual",
                  status: lead.status,
                  observacoes: lead.observacoes || "",
                  interesse: lead.interest || "",
                });
                setShowModal(true);
              }}
              className="rounded-3xl border-2 border-slate-200 bg-white p-6 shadow-soft cursor-pointer hover:border-brand transition"
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">{lead.name}</h3>
                <span className={`rounded-full px-2 py-1 text-xs font-semibold uppercase ${getStatusColor(lead.status)}`}>
                  {lead.status}
                </span>
              </div>
              {lead.phone && (
                <div className="mb-2 text-sm text-slate-600">📞 {lead.phone}</div>
              )}
              {lead.email && (
                <div className="mb-2 text-sm text-slate-600">✉️ {lead.email}</div>
              )}
              {lead.observacoes && (
                <div className="text-sm text-slate-600 truncate">
                  {lead.observacoes}
                </div>
              )}
              <div className="mt-2 flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(lead.id);
                  }}
                  className="rounded-xl bg-red-100 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-200"
                >
                  Excluir
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-[32px] bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-serif font-semibold text-slate-900">
                {selectedLead ? "Editar Lead" : "Novo Lead"}
              </h2>
              <button
                onClick={() => {
                  setShowModal(false);
                  setSelectedLead(null);
                }}
                className="text-2xl text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>

            <form onSubmit={save} className="space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Nome *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="input mt-1"
                  required
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-500">Telefone</label>
                  <input
                    type="text"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-slate-500">Email</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="input mt-1"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Origem</label>
                <select
                  value={form.origem}
                  onChange={(e) => setForm({ ...form, origem: e.target.value })}
                  className="input mt-1"
                >
                  <option value="manual">Manual</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="telegram">Telegram</option>
                  <option value="site">Site</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="input mt-1"
                >
                  <option value="Novo lead">Novo lead</option>
                  <option value="Em atendimento">Em atendimento</option>
                  <option value="Aguardando resposta">Aguardando resposta</option>
                  <option value="Orçamento enviado">Orçamento enviado</option>
                  <option value="Fechado">Fechado</option>
                  <option value="Perdido">Perdido</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Observações</label>
                <textarea
                  value={form.observacoes}
                  onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
                  className="input mt-1"
                  rows={3}
                />
              </div>

              {saved && (
                <div className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                  ✅ Salvo com sucesso!
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setSelectedLead(null);
                  }}
                  className="flex-1 rounded-2xl bg-slate-100 px-5 py-2 text-sm hover:bg-slate-200"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-2xl bg-brand px-5 py-2 font-semibold text-white hover:bg-brand/90"
                >
                  {selectedLead ? "Salvar" : "Criar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
