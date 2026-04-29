import { FormEvent, useEffect, useState } from "react";
import {
  createCrmTag,
  deleteCrmTag,
  getCrmSettings,
  getCrmTags,
  updateCrmSettings,
} from "../api";
import type { CrmSettings, CrmTag } from "../types";

const TAG_COLORS = [
  "#10b981", "#3b82f6", "#8b5cf6", "#f59e0b",
  "#ef4444", "#ec4899", "#14b8a6", "#f97316",
  "#64748b", "#1d4ed8",
];

export default function CrmSettingsPage() {
  const [settings, setSettings] = useState<CrmSettings | null>(null);
  const [tags, setTags] = useState<CrmTag[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // Tag form
  const [tagName, setTagName] = useState("");
  const [tagColor, setTagColor] = useState(TAG_COLORS[0]);
  const [addingTag, setAddingTag] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [s, t] = await Promise.all([getCrmSettings(), getCrmTags()]);
      setSettings(s);
      setTags(t);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function saveSettings(e: FormEvent) {
    e.preventDefault();
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateCrmSettings({
        initial_auto_message: settings.mensagem_inicial || "",
        hermes_enabled: settings.hermes_ativo,
      });
      setSettings(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  }

  async function handleAddTag(e: FormEvent) {
    e.preventDefault();
    if (!tagName.trim()) return;
    setAddingTag(true);
    try {
      const tag = await createCrmTag({ name: tagName.trim(), color: tagColor });
      setTags((prev) => [...prev, tag]);
      setTagName("");
    } finally {
      setAddingTag(false);
    }
  }

  async function handleDeleteTag(id: number) {
    if (!confirm("Excluir esta tag? Ela será removida de todos os leads.")) return;
    await deleteCrmTag(id);
    setTags((prev) => prev.filter((t) => t.id !== id));
  }

  if (loading || !settings) {
    return <div className="py-20 text-center text-slate-400">Carregando...</div>;
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="font-serif text-3xl text-ink">Configurações do CRM</h1>
        <p className="mt-1 text-sm text-slate-500">Personalize o comportamento do CRM para seu negócio</p>
      </div>

      {/* Configurações gerais */}
      <form onSubmit={saveSettings} className="rounded-[28px] bg-white p-6 shadow-soft space-y-5">
        <h2 className="font-serif text-xl text-ink">Geral</h2>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Horário de atendimento — início</label>
            <input
              type="time"
              className="input mt-1"
              value={settings.horario_inicio}
              onChange={(e) => setSettings({ ...settings, horario_inicio: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Horário de atendimento — fim</label>
            <input
              type="time"
              className="input mt-1"
              value={settings.horario_fim}
              onChange={(e) => setSettings({ ...settings, horario_fim: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold uppercase text-slate-500">Mensagem automática inicial</label>
          <textarea
            className="input mt-1"
            rows={3}
            value={settings.mensagem_inicial ?? ""}
            onChange={(e) => setSettings({ ...settings, mensagem_inicial: e.target.value || null })}
            placeholder="Olá! Seja bem-vindo. Como posso ajudar?"
          />
          <p className="mt-1 text-xs text-slate-400">Enviada quando um novo contato entra pela primeira vez.</p>
        </div>

        <div className="flex flex-col gap-3">
          <label className="flex cursor-pointer items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-ink">Hermes (IA) ativo no CRM</div>
              <div className="text-xs text-slate-500">Respostas automáticas via IA nas conversas do CRM</div>
            </div>
            <div
              onClick={() => setSettings({ ...settings, hermes_ativo: !settings.hermes_ativo })}
              className={`relative h-6 w-11 rounded-full transition-colors ${settings.hermes_ativo ? "bg-violet-600" : "bg-slate-300"}`}
            >
              <div className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${settings.hermes_ativo ? "translate-x-5" : "translate-x-0.5"}`} />
            </div>
          </label>

          <label className="flex cursor-pointer items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-ink">Notificar follow-ups via Telegram</div>
              <div className="text-xs text-slate-500">Receba lembretes de follow-up no seu Telegram pessoal</div>
            </div>
            <div
              onClick={() => setSettings({ ...settings, notificar_followup_telegram: !settings.notificar_followup_telegram })}
              className={`relative h-6 w-11 rounded-full transition-colors ${settings.notificar_followup_telegram ? "bg-violet-600" : "bg-slate-300"}`}
            >
              <div className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${settings.notificar_followup_telegram ? "translate-x-5" : "translate-x-0.5"}`} />
            </div>
          </label>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <button
            type="submit"
            disabled={saving}
            className="rounded-2xl bg-violet-600 px-6 py-2.5 font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Salvar configurações"}
          </button>
          {saved && <span className="text-sm text-emerald-600 font-medium">✓ Salvo!</span>}
        </div>
      </form>

      {/* Tags */}
      <div className="rounded-[28px] bg-white p-6 shadow-soft space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-xl text-ink">Tags</h2>
          <span className="text-xs text-slate-400">{tags.length} tag{tags.length !== 1 ? "s" : ""}</span>
        </div>

        {/* Lista de tags existentes */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium"
                style={{ borderColor: tag.color, color: tag.color, backgroundColor: `${tag.color}15` }}
              >
                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: tag.color }} />
                {tag.name}
                <button
                  onClick={() => handleDeleteTag(tag.id)}
                  className="ml-1 rounded-full text-xs opacity-50 hover:opacity-100"
                  title="Excluir tag"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Adicionar nova tag */}
        <form onSubmit={handleAddTag} className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[160px]">
            <label className="text-xs font-semibold uppercase text-slate-500">Nome da nova tag</label>
            <input
              className="input mt-1"
              value={tagName}
              onChange={(e) => setTagName(e.target.value)}
              placeholder="Ex: quente, urgente..."
              maxLength={30}
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase text-slate-500">Cor</label>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {TAG_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setTagColor(c)}
                  className={`h-6 w-6 rounded-full transition ${tagColor === c ? "ring-2 ring-offset-1 ring-slate-400" : ""}`}
                  style={{ backgroundColor: c }}
                  title={c}
                />
              ))}
            </div>
          </div>
          <button
            type="submit"
            disabled={addingTag || !tagName.trim()}
            className="rounded-2xl px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
            style={{ backgroundColor: tagColor }}
          >
            {addingTag ? "..." : "+ Adicionar"}
          </button>
        </form>

        {tags.length === 0 && (
          <p className="text-sm text-slate-400">
            Nenhuma tag criada ainda. Use tags para classificar leads: quente, frio, urgente, cliente antigo, etc.
          </p>
        )}
      </div>
    </div>
  );
}
