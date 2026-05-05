/**
 * Painel Master — só pra super admin (você, dono do SaaS).
 * Lista todos os tenants (clientes) e permite criar novos.
 */
import { FormEvent, useEffect, useState } from "react";
import {
  addAdminCredits,
  createAdminTenant,
  deleteAdminTenant,
  getAdminTenants,
  getMasterBotInfo,
  setAdminTenantModules,
  updateAdminTenant,
  type MasterBotInfo,
} from "./api";
import { NICHE_TEMPLATES } from "./niches";
import type { AdminTenant, NicheTemplate } from "./types";
import {
  hermesAdminChat,
  getHermesAdminDashboard,
  getAdminTasks,
  getAdminProjects,
  getAdminRoutines,
  getAdminMemory,
  getAdminActionLogs,
  getAdminSkills,
  createAdminTask,
  createAdminProject,
  createAdminRoutine,
  createAdminMemory,
  updateAdminTask,
  updateAdminProject,
  updateAdminRoutine,
  deleteAdminRoutine,
  createAdminSkill,
  updateAdminSkill,
  deleteAdminSkill,
  runAdminSkill,
  suggestAdminSkill,
} from "./api";
import type {
  HermesAdminChatResponse,
  AdminTask,
  AdminProject,
  AdminRoutine,
  AdminMemory,
  AdminActionLog,
  AdminSkill,
  HermesAdminDashboard,
} from "./types";

function genPassword(): string {
  return "Senha" + Math.floor(1000 + Math.random() * 9000) + "!";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR");
}

function pct(t: AdminTenant): number {
  if (!t.credits_total || !t.credits_remaining) return 0;
  return Math.max(0, Math.min(100, (t.credits_remaining / t.credits_total) * 100));
}

function pctColor(t: AdminTenant): string {
  const p = pct(t);
  if (p === 0) return "bg-red-600";
  if (p <= 10) return "bg-amber-500";
  return "bg-emerald-600";
}

export default function MasterPanel() {
  const [tenants, setTenants] = useState<AdminTenant[]>([]);
  const [masterBot, setMasterBot] = useState<MasterBotInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [qrTenant, setQrTenant] = useState<AdminTenant | null>(null);
  const [showHermesAdmin, setShowHermesAdmin] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [tenantsData, botData] = await Promise.all([
        getAdminTenants(),
        getMasterBotInfo().catch(() => null),
      ]);
      setTenants(tenantsData);
      setMasterBot(botData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const totalRevenue = tenants
    .filter((t) => t.active)
    .reduce((acc) => acc + 297, 0); // mock R$ 297/mês por tenant ativo
  const totalUsedMessages = tenants.reduce((acc, t) => acc + (t.credits_used || 0), 0);
  const blocked = tenants.filter((t) => (t.credits_remaining || 0) <= 0).length;

  return (
    <div className="space-y-6">
      {masterBot && !masterBot.configured && (
        <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-4 text-sm">
          <strong className="text-amber-900">⚠️ Bot mestre não configurado.</strong>
          <span className="ml-2 text-amber-800">
            Defina <code className="rounded bg-amber-100 px-1">HERMES_MASTER_BOT_TOKEN</code> e{" "}
            <code className="rounded bg-amber-100 px-1">HERMES_MASTER_BOT_USERNAME</code> nas
            envs do Coolify pra clientes sem bot dedicado funcionarem.
          </span>
        </div>
      )}
      {masterBot && masterBot.configured && (
        <div className="rounded-2xl border-2 border-emerald-300 bg-emerald-50 p-4 text-sm">
          <strong className="text-emerald-900">✅ Bot mestre ativo:</strong>{" "}
          <a
            href={`https://t.me/${(masterBot.username || "").replace("@", "")}`}
            target="_blank"
            rel="noreferrer"
            className="font-mono text-emerald-700 hover:underline"
          >
            @{(masterBot.username || "").replace("@", "")}
          </a>
          <span className="ml-2 text-emerald-800">
            — atende todos os tenants automaticamente via deep link.
          </span>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Clientes ativos" value={tenants.filter((t) => t.active).length} />
        <Stat label="Bloqueados" value={blocked} color="red" />
        <Stat label="Mensagens (mês)" value={totalUsedMessages.toLocaleString("pt-BR")} />
        <Stat
          label="Receita estimada"
          value={`R$ ${totalRevenue.toLocaleString("pt-BR")}`}
          color="emerald"
        />
      </div>

      <div className="rounded-2xl border-2 border-dashed border-violet-200 bg-violet-50 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-violet-900">🤖 Hermes Admin</h3>
            <p className="text-sm text-violet-700">
              Assistente de IA para gerenciar sua plataforma
            </p>
          </div>
          <button
            onClick={() => setShowHermesAdmin(true)}
            className="rounded-full bg-violet-600 px-6 py-3 text-sm font-semibold text-white hover:bg-violet-700"
          >
            Abrir Hermes Admin
          </button>
        </div>
      </div>

      <div className="rounded-[32px] bg-white p-6 shadow-soft">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">Clientes (Tenants)</h2>
          <button
            onClick={() => setShowForm(true)}
            className="rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            + Novo cliente
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        {loading ? (
          <div className="py-8 text-center text-slate-500">Carregando...</div>
        ) : tenants.length === 0 ? (
          <div className="rounded-2xl bg-panel py-10 text-center text-sm text-slate-500">
            Nenhum cliente ainda. Clique em "+ Novo cliente" pra começar a vender.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2">Cliente</th>
                  <th className="px-3 py-2">Nicho</th>
                  <th className="px-3 py-2">Plano</th>
                  <th className="px-3 py-2">Mensagens</th>
                  <th className="px-3 py-2">Bot</th>
                  <th className="px-3 py-2">Módulos</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Ações</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((t) => {
                  const niche = NICHE_TEMPLATES.find((n) => n.id === t.niche);
                  return (
                    <tr key={t.id} className="border-t border-black/5">
                      <td className="px-3 py-3">
                        <div className="font-medium">{t.name}</div>
                        <div className="text-xs text-slate-500">{t.email}</div>
                      </td>
                      <td className="px-3 py-3">
                        {niche ? `${niche.emoji} ${niche.label}` : "—"}
                      </td>
                      <td className="px-3 py-3 capitalize">{t.plan}</td>
                      <td className="px-3 py-3">
                        <div className="text-xs">
                          {(t.credits_remaining || 0).toLocaleString("pt-BR")} /{" "}
                          {(t.credits_total || 0).toLocaleString("pt-BR")}
                        </div>
                        <div className="mt-1 h-1.5 w-24 overflow-hidden rounded-full bg-slate-200">
                          <div
                            className={`h-full ${pctColor(t)}`}
                            style={{ width: `${pct(t)}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-3 py-3 text-xs">
                        {t.telegram_bot_username ? (
                          <a
                            href={`https://t.me/${t.telegram_bot_username.replace("@", "")}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-emerald-700 hover:underline"
                          >
                            @{t.telegram_bot_username.replace("@", "")}
                          </a>
                        ) : (
                          <span className="text-slate-400">não config</span>
                        )}
                      </td>
                      {/* Módulos */}
                      <td className="px-3 py-3">
                        <div className="flex flex-wrap gap-1">
                          {[
                            { key: "crm", label: "CRM" },
                            { key: "whatsapp", label: "WhatsApp" },
                            { key: "kanban", label: "Kanban" },
                            { key: "agenda", label: "Agenda" },
                            { key: "instagram", label: "Instagram" },
                            { key: "youtube", label: "YouTube" },
                          ].map((mod) => (
                            <button
                              key={mod.key}
                              onClick={async () => {
                                await setAdminTenantModules(t.id, { [mod.key]: !(t as any)[`${mod.key}_enabled`] });
                                load();
                              }}
                              title={(t as any)[`${mod.key}_enabled`] ? `Desativar ${mod.label}` : `Ativar ${mod.label}`}
                              className={`flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold uppercase transition ${
                                (t as any)[`${mod.key}_enabled`]
                                  ? "bg-violet-100 text-violet-700 hover:bg-violet-200"
                                  : "bg-slate-100 text-slate-400 hover:bg-slate-200"
                              }`}
                            >
                              {(t as any)[`${mod.key}_enabled`] ? `✓ ${mod.label}` : `○ ${mod.label}`}
                            </button>
                          ))}
                        </div>
                      </td>

                      <td className="px-3 py-3">
                        {!t.active ? (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] uppercase text-red-700">
                            Inativo
                          </span>
                        ) : (t.credits_remaining || 0) <= 0 ? (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] uppercase text-red-700">
                            Bloqueado
                          </span>
                        ) : (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] uppercase text-emerald-700">
                            Ativo
                          </span>
                        )}
                      </td>
                      <td className="space-x-1 px-3 py-3 text-xs">
                        <button
                          onClick={() => setQrTenant(t)}
                          className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200"
                          title="Ver QR Code do bot"
                        >
                          QR
                        </button>
                        <button
                          onClick={async () => {
                            const v = prompt("Adicionar quantas mensagens?", "1000");
                            if (!v) return;
                            await addAdminCredits(t.id, parseInt(v, 10));
                            load();
                          }}
                          className="rounded bg-emerald-100 px-2 py-1 text-emerald-700 hover:bg-emerald-200"
                        >
                          + Créditos
                        </button>
                        <button
                          onClick={async () => {
                            await updateAdminTenant(t.id, { active: !t.active });
                            load();
                          }}
                          className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200"
                        >
                          {t.active ? "Pausar" : "Ativar"}
                        </button>
                        <button
                          onClick={async () => {
                            if (!confirm(`Excluir ${t.name}? Vai apagar TODAS as conversas dele.`)) return;
                            await deleteAdminTenant(t.id);
                            load();
                          }}
                          className="rounded bg-red-100 px-2 py-1 text-red-700 hover:bg-red-200"
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showForm && (
        <CreateTenantModal
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false);
            load();
          }}
        />
      )}

      {qrTenant && (
        <QRCodeModal
          tenant={qrTenant}
          masterBot={masterBot}
          onClose={() => setQrTenant(null)}
        />
      )}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string | number; color?: "red" | "emerald" }) {
  return (
    <div
      className={`rounded-[28px] p-6 shadow-soft backdrop-blur ${
        color === "red" ? "bg-red-50" : color === "emerald" ? "bg-emerald-50" : "bg-white/80"
      }`}
    >
      <div className="text-sm text-slate-500">{label}</div>
      <div
        className={`mt-3 text-3xl font-semibold ${
          color === "red" ? "text-red-600" : color === "emerald" ? "text-emerald-700" : "text-ink"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function CreateTenantModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [niche, setNiche] = useState<NicheTemplate | null>(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    plan: "starter",
    credits: 1000,
    user_name: "",
    user_email: "",
    user_password: genPassword(),
    telegram_bot_token: "",
    telegram_bot_username: "",
    system_prompt: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function pickNiche(n: NicheTemplate) {
    setNiche(n);
    setForm((f) => ({
      ...f,
      plan: n.defaultPlan,
      credits: n.defaultCredits,
      system_prompt: n.systemPrompt,
    }));
    setStep(2);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createAdminTenant({
        name: form.name,
        email: form.email,
        plan: form.plan,
        niche: niche?.id || null,
        system_prompt: form.system_prompt || null,
        telegram_bot_token: form.telegram_bot_token || null,
        telegram_bot_username: form.telegram_bot_username || null,
        credits: form.credits,
        user_name: form.user_name || form.name,
        user_email: form.user_email,
        user_password: form.user_password,
      });
      setStep(3);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-[32px] bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">
            {step === 1 && "Escolha o nicho"}
            {step === 2 && `Configurar ${niche?.label}`}
            {step === 3 && "✅ Cliente criado!"}
          </h2>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">
            ×
          </button>
        </div>

        {step === 1 && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
            {NICHE_TEMPLATES.map((n) => (
              <button
                key={n.id}
                onClick={() => pickNiche(n)}
                className="flex flex-col items-center gap-1 rounded-2xl border-2 border-slate-100 p-4 text-center transition hover:border-emerald-500 hover:bg-emerald-50"
              >
                <div className="text-3xl">{n.emoji}</div>
                <div className="text-sm font-medium">{n.label}</div>
                <div className="text-xs text-slate-500">{n.defaultCredits.toLocaleString("pt-BR")} msgs</div>
              </button>
            ))}
          </div>
        )}

        {step === 2 && niche && (
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">Empresa</label>
              <input
                className="input mt-1"
                placeholder="ex: Barbearia Corte Real"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Email da empresa</label>
                <input
                  className="input mt-1"
                  type="email"
                  placeholder="contato@empresa.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Plano</label>
                <select
                  className="input mt-1"
                  value={form.plan}
                  onChange={(e) => setForm({ ...form, plan: e.target.value })}
                >
                  <option value="starter">Starter</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Mensagens/mês</label>
                <input
                  className="input mt-1"
                  type="number"
                  value={form.credits}
                  onChange={(e) => setForm({ ...form, credits: parseInt(e.target.value, 10) })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Senha (anote!)</label>
                <input
                  className="input mt-1"
                  value={form.user_password}
                  onChange={(e) => setForm({ ...form, user_password: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Login (email do cliente)</label>
                <input
                  className="input mt-1"
                  type="email"
                  value={form.user_email}
                  onChange={(e) => setForm({ ...form, user_email: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-slate-500">Nome do cliente</label>
                <input
                  className="input mt-1"
                  value={form.user_name}
                  onChange={(e) => setForm({ ...form, user_name: e.target.value })}
                  placeholder="(opcional - usa o nome da empresa)"
                />
              </div>
            </div>
            <div className="rounded-2xl border-2 border-dashed border-slate-200 p-4">
              <div className="mb-2 text-xs font-semibold uppercase text-slate-500">
                🤖 Bot Dedicado (opcional — premium)
              </div>
              <p className="mb-3 text-xs text-slate-500">
                Por padrão usa o <strong>bot mestre</strong> com deep link. Preencha aqui só se
                este cliente paga premium e quer um bot exclusivo (você cria no @BotFather).
              </p>
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  className="input"
                  placeholder="Token do BotFather"
                  value={form.telegram_bot_token}
                  onChange={(e) => setForm({ ...form, telegram_bot_token: e.target.value })}
                />
                <input
                  className="input"
                  placeholder="Username (sem @)"
                  value={form.telegram_bot_username}
                  onChange={(e) => setForm({ ...form, telegram_bot_username: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold uppercase text-slate-500">
                Personalidade do agente (system prompt)
              </label>
              <textarea
                className="input mt-1 font-mono text-xs"
                rows={8}
                value={form.system_prompt}
                onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              />
              <p className="mt-1 text-xs text-slate-500">
                Edite acima pra personalizar com nome, endereço, preços, horários do cliente.
              </p>
            </div>
            {error && (
              <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
            )}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="rounded-2xl bg-slate-100 px-5 py-2 text-sm hover:bg-slate-200"
              >
                ← Voltar
              </button>
              <button
                type="submit"
                disabled={saving}
                className="flex-1 rounded-2xl bg-emerald-600 px-5 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {saving ? "Criando..." : "Criar cliente"}
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <div className="rounded-2xl bg-emerald-50 p-5">
              <p className="text-sm text-emerald-900 font-semibold">
                ✅ Cliente criado! Manda as credenciais:
              </p>
              <div className="mt-3 space-y-2 rounded-xl bg-white p-4 font-mono text-xs">
                <div>🌐 Painel: https://meuchat.fbautomacao.space</div>
                <div>📧 Login: {form.user_email}</div>
                <div>🔑 Senha: {form.user_password}</div>
                {form.telegram_bot_username && (
                  <div>🤖 Bot dedicado: https://t.me/{form.telegram_bot_username.replace("@", "")}</div>
                )}
              </div>
              <p className="mt-3 text-xs text-emerald-800">
                💡 O QR Code (com link do bot mestre + identificação do cliente) está disponível na
                tabela. Clique em "QR" na linha do cliente.
              </p>
            </div>
            <button
              onClick={onCreated}
              className="w-full rounded-2xl bg-emerald-600 px-5 py-3 font-semibold text-white hover:bg-emerald-700"
            >
              Concluir
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function QRCodeModal({
  tenant,
  masterBot,
  onClose,
}: {
  tenant: AdminTenant;
  masterBot: MasterBotInfo | null;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<"web" | "telegram">("web");

  const panelUrl = masterBot?.panel_url || "https://meuchat.fbautomacao.space";
  const webLink = `${panelUrl}/c/${tenant.id}`;

  const dedicatedUsername = (tenant.telegram_bot_username || "").replace("@", "");
  const masterUsername = (masterBot?.username || "").replace("@", "");
  const usingDedicated = !!dedicatedUsername;
  const tgUsername = usingDedicated ? dedicatedUsername : masterUsername;
  const tgLink = !tgUsername
    ? ""
    : usingDedicated
      ? `https://t.me/${tgUsername}`
      : `https://t.me/${tgUsername}?start=tenant_${tenant.id}`;

  const link = tab === "web" ? webLink : tgLink;
  const qrUrl = link
    ? `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(link)}`
    : "";

  const slug = tenant.name.toLowerCase().replace(/\s+/g, "-");
  const downloadName = `qr-${slug}-${tab}.png`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-[32px] bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-serif text-2xl">QR Code</h2>
            <p className="text-sm text-slate-500">{tenant.name}</p>
          </div>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">
            ×
          </button>
        </div>

        {/* Tabs Web / Telegram */}
        <div className="mb-4 flex gap-2 rounded-xl bg-slate-100 p-1">
          <button
            onClick={() => setTab("web")}
            className={`flex-1 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              tab === "web" ? "bg-white shadow text-emerald-700" : "text-slate-600"
            }`}
          >
            🌐 Chat Web
          </button>
          <button
            onClick={() => setTab("telegram")}
            className={`flex-1 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              tab === "telegram" ? "bg-white shadow text-emerald-700" : "text-slate-600"
            }`}
          >
            ✈️ Telegram
          </button>
        </div>

        {tab === "telegram" && !tgLink ? (
          <div className="rounded-2xl bg-amber-50 p-5 text-sm text-amber-800">
            ⚠️ Bot Telegram não configurado. Defina{" "}
            <code className="rounded bg-amber-100 px-1">HERMES_MASTER_BOT_USERNAME</code> nas
            envs ou cadastre um bot dedicado pra este tenant.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-xl bg-emerald-50 p-3 text-xs text-emerald-800">
              {tab === "web" ? (
                <>
                  🟢 <strong>Chat web</strong> — abre direto no navegador, sem precisar de
                  Telegram. Recomendado!
                </>
              ) : usingDedicated ? (
                <>
                  🟣 <strong>Bot Telegram dedicado</strong> — branding próprio do cliente
                </>
              ) : (
                <>
                  ✈️ <strong>Bot Telegram mestre</strong> — identifica via deep link
                </>
              )}
            </div>

            <div className="flex justify-center rounded-2xl bg-slate-50 p-6">
              <img src={qrUrl} alt="QR Code" className="h-64 w-64" />
            </div>

            <div className="space-y-2 rounded-xl bg-slate-50 p-4 text-sm">
              <div className="text-xs font-semibold uppercase text-slate-500">Link:</div>
              <a
                href={link}
                target="_blank"
                rel="noreferrer"
                className="break-all text-emerald-700 hover:underline"
              >
                {link}
              </a>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(link);
                  alert("Link copiado!");
                }}
                className="flex-1 rounded-2xl bg-slate-100 px-5 py-2 text-sm font-medium hover:bg-slate-200"
              >
                📋 Copiar link
              </button>
              <a
                href={qrUrl}
                download={downloadName}
                className="flex-1 rounded-2xl bg-emerald-600 px-5 py-2 text-center text-sm font-semibold text-white hover:bg-emerald-700"
              >
                ⬇ Baixar QR
              </a>
            </div>

            <p className="text-xs text-slate-500">
              {tab === "web" ? (
                <>
                  Quem escanear abre o chat <strong>direto no navegador</strong>, sem precisar
                  de app instalado. Funciona em qualquer celular.
                </>
              ) : (
                <>
                  Quem escanear abre o Telegram já no bot. Cliente final precisa ter o app
                  instalado.
                </>
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function HermesAdminPanel({ onClose }: { onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<
    "chat" | "tasks" | "projects" | "routines" | "memory" | "logs"
  >("chat");
  const [messages, setMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState<HermesAdminDashboard | null>(null);
  const [tasks, setTasks] = useState<AdminTask[]>([]);
  const [projects, setProjects] = useState<AdminProject[]>([]);
  const [routines, setRoutines] = useState<AdminRoutine[]>([]);
  const [memories, setMemories] = useState<AdminMemory[]>([]);
  const [logs, setLogs] = useState<AdminActionLog[]>([]);
  const [skills, setSkills] = useState<AdminSkill[]>([]);

  const loadTasks = async () => {
    try {
      const data = await getAdminTasks();
      setTasks(data.tasks);
    } catch (e) {
      console.error(e);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await getAdminProjects();
      setProjects(data.projects);
    } catch (e) {
      console.error(e);
    }
  };

  const loadRoutines = async () => {
    try {
      const data = await getAdminRoutines();
      setRoutines(data.routines);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMemory = async () => {
    try {
      const data = await getAdminMemory();
      setMemories(data.memories);
    } catch (e) {
      console.error(e);
    }
  };

  const loadLogs = async () => {
    try {
      const data = await getAdminActionLogs();
      setLogs(data.logs);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSkills = async () => {
    try {
      const data = await getAdminSkills();
      setSkills(data.skills);
    } catch (e) {
      console.error(e);
    }
  };

  const loadDashboard = async () => {
    try {
      const data = await getHermesAdminDashboard();
      setDashboard(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadTasks();
    loadProjects();
    loadRoutines();
    loadMemory();
    loadLogs();
    loadSkills();
    loadDashboard();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const response = await hermesAdminChat(userMessage);

      setMessages((prev) => [...prev, { role: "assistant", content: response.response || response.message || "Sem resposta" }]);

      if (response.dashboard) {
        setDashboard(response.dashboard);
      }

      if (response.suggested_skills && response.suggested_skills.length > 0) {
        alert(`Sugestão de skill: ${response.suggested_skills[0].suggestion.name}`);
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Não consegui concluir a chamada do assistente.\n${e instanceof Error ? e.message : "Falha interna"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    const title = prompt("Título da tarefa:");
    if (!title) return;
    const description = prompt("Descrição da tarefa:");
    if (!description) return;

    try {
      await createAdminTask({ title, description });
      loadTasks();
      alert("Tarefa criada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao criar tarefa.");
    }
  };

  const handleUpdateTask = async (task: AdminTask) => {
    const newStatus = prompt(
      "Novo status (pending, in_progress, completed):",
      task.status
    );
    if (!newStatus) return;

    try {
      await updateAdminTask(task.id, { status: newStatus as any });
      loadTasks();
    } catch (e) {
      console.error(e);
      alert("Erro ao atualizar tarefa.");
    }
  };

  const handleCreateProject = async () => {
    const name = prompt("Nome do projeto:");
    if (!name) return;
    const description = prompt("Descrição do projeto:");
    if (!description) return;

    try {
      await createAdminProject({ name, description });
      loadProjects();
      alert("Projeto criado!");
    } catch (e) {
      console.error(e);
      alert("Erro ao criar projeto.");
    }
  };

  const handleCreateRoutine = async () => {
    const name = prompt("Nome da rotina:");
    if (!name) return;
    const description = prompt("Descrição da rotina:");
    if (!description) return;
    const schedule = prompt("Agendamento (ex: 0 9 * * *):");
    if (!schedule) return;

    try {
      await createAdminRoutine({ name, description, schedule_type: "cron", schedule_value: 0 });
      loadRoutines();
      alert("Rotina criada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao criar rotina.");
    }
  };

  const handleRunRoutine = async (routine: AdminRoutine) => {
    try {
      await deleteAdminRoutine(routine.id);
      alert("Rotina executada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao executar rotina.");
    }
  };

  const handleCreateMemory = async () => {
    const key = prompt("Chave da memória:");
    if (!key) return;
    const value = prompt("Valor da memória:");
    if (!value) return;

    try {
      await createAdminMemory({ category: "general", key, value });
      loadMemory();
      alert("Memória criada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao criar memória.");
    }
  };

  const handleCreateSkill = async () => {
    const name = prompt("Nome da skill:");
    if (!name) return;
    const description = prompt("Descrição da skill:");
    if (!description) return;
    const instructions = prompt("Instruções da skill:");
    if (!instructions) return;

    try {
      await createAdminSkill({
        name,
        description,
        trigger_type: "manual",
        trigger_value: "",
        instructions,
      });
      loadSkills();
      alert("Skill criada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao criar skill.");
    }
  };

  const handleRunSkill = async (skill: AdminSkill) => {
    try {
      await runAdminSkill(skill.id);
      alert("Skill executada!");
    } catch (e) {
      console.error(e);
      alert("Erro ao executar skill.");
    }
  };

  const handleSuggestSkill = async () => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage || lastMessage.role !== "assistant") {
      alert("Primeiro converse com o Hermes Admin!");
      return;
    }

    try {
      const suggestion = await suggestAdminSkill(lastMessage.content);
      if (suggestion) {
        const confirmCreate = confirm(
          `Criar skill "${suggestion.suggestion.name}"?\n\nDescrição: ${suggestion.suggestion.description}\n\nInstruções: ${suggestion.suggestion.instructions}`
        );
        if (confirmCreate) {
          await createAdminSkill({
            name: suggestion.suggestion.name,
            description: suggestion.suggestion.description || undefined,
            trigger_type: "manual",
            trigger_value: "",
            instructions: suggestion.suggestion.instructions,
          });
          loadSkills();
          alert("Skill criada!");
        }
      } else {
        alert("Nenhuma sugestão de skill encontrada.");
      }
    } catch (e) {
      console.error(e);
      alert("Erro ao sugerir skill.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="h-[90vh] w-full max-w-6xl overflow-hidden rounded-3xl bg-white shadow-2xl">
        <div className="flex h-full">
          <div className="flex w-64 flex-col border-r border-slate-200 bg-slate-50 p-4">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900">🤖 Hermes Admin</h2>
              <p className="text-xs text-slate-500">Assistente de gerenciamento</p>
            </div>

            <nav className="space-y-1">
              {[
                { id: "chat" as const, label: "💬 Chat", icon: "💬" },
                { id: "tasks" as const, label: "📋 Tarefas", icon: "📋" },
                { id: "projects" as const, label: "📁 Projetos", icon: "📁" },
                { id: "routines" as const, label: "⚙️ Rotinas", icon: "⚙️" },
                { id: "memory" as const, label: "🧠 Memória", icon: "🧠" },
                { id: "logs" as const, label: "📊 Logs", icon: "📊" },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                    activeTab === item.id
                      ? "bg-violet-100 text-violet-900"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </nav>

            <div className="mt-auto space-y-2">
              <button
                onClick={handleSuggestSkill}
                className="w-full rounded-xl bg-emerald-100 px-4 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-200"
              >
                ✨ Criar Skill do Chat
              </button>
              <button
                onClick={onClose}
                className="w-full rounded-xl bg-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-300"
              >
                ✕ Fechar
              </button>
            </div>
          </div>

          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="border-b border-slate-200 p-4">
              {activeTab === "chat" && (
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Conversa</h3>
                  <p className="text-sm text-slate-500">
                    Converse com o Hermes Admin para gerenciar sua plataforma
                  </p>
                </div>
              )}
              {activeTab === "tasks" && (
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Tarefas</h3>
                    <p className="text-sm text-slate-500">{tasks.length} tarefas</p>
                  </div>
                  <button
                    onClick={handleCreateTask}
                    className="rounded-full bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700"
                  >
                    + Nova Tarefa
                  </button>
                </div>
              )}
              {activeTab === "projects" && (
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Projetos</h3>
                    <p className="text-sm text-slate-500">{projects.length} projetos</p>
                  </div>
                  <button
                    onClick={handleCreateProject}
                    className="rounded-full bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700"
                  >
                    + Novo Projeto
                  </button>
                </div>
              )}
              {activeTab === "routines" && (
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Rotinas</h3>
                    <p className="text-sm text-slate-500">{routines.length} rotinas</p>
                  </div>
                  <button
                    onClick={handleCreateRoutine}
                    className="rounded-full bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700"
                  >
                    + Nova Rotina
                  </button>
                </div>
              )}
              {activeTab === "memory" && (
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Memória</h3>
                    <p className="text-sm text-slate-500">{memories.length} memórias</p>
                  </div>
                  <button
                    onClick={handleCreateMemory}
                    className="rounded-full bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700"
                  >
                    + Nova Memória
                  </button>
                </div>
              )}
              {activeTab === "logs" && (
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Logs de Ações</h3>
                  <p className="text-sm text-slate-500">{logs.length} ações registradas</p>
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === "chat" && (
                <div className="flex h-full flex-col">
                  <div className="flex-1 space-y-4 overflow-y-auto">
                    {messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`rounded-2xl p-4 ${
                          msg.role === "user"
                            ? "bg-violet-600 text-white"
                            : "bg-slate-100 text-slate-900"
                        }`}
                      >
                        <div className="text-sm font-semibold">
                          {msg.role === "user" ? "Você" : "Hermes Admin"}
                        </div>
                        <div className="mt-1 whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    ))}
                    {loading && (
                      <div className="rounded-2xl bg-slate-100 p-4 text-slate-500">
                        Hermes Admin está pensando...
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && handleSend()}
                      placeholder="Digite sua mensagem..."
                      className="flex-1 rounded-xl border border-slate-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                      disabled={loading}
                    />
                    <button
                      onClick={handleSend}
                      disabled={loading}
                      className="rounded-xl bg-violet-600 px-6 py-2 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
                    >
                      Enviar
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "tasks" && (
                <div className="space-y-3">
                  {tasks.length === 0 ? (
                    <div className="text-center text-sm text-slate-500">
                      Nenhuma tarefa ainda
                    </div>
                  ) : (
                    tasks.map((task) => (
                      <div
                        key={task.id}
                        className="rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-slate-900">{task.title}</h4>
                            <p className="text-sm text-slate-600">{task.description}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`rounded-full px-2 py-1 text-[10px] font-semibold uppercase ${
                                task.status === "completed"
                                  ? "bg-emerald-100 text-emerald-900"
                                  : task.status === "in_progress"
                                    ? "bg-amber-100 text-amber-900"
                                    : "bg-slate-100 text-slate-900"
                              }`}
                            >
                              {task.status}
                            </span>
                            <button
                              onClick={() => handleUpdateTask(task)}
                              className="rounded-lg bg-slate-100 px-2 py-1 text-xs hover:bg-slate-200"
                            >
                              Editar
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "projects" && (
                <div className="space-y-3">
                  {projects.length === 0 ? (
                    <div className="text-center text-sm text-slate-500">
                      Nenhum projeto ainda
                    </div>
                  ) : (
                    projects.map((project) => (
                      <div
                        key={project.id}
                        className="rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <h4 className="font-semibold text-slate-900">{project.name}</h4>
                        <p className="text-sm text-slate-600">{project.description}</p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "routines" && (
                <div className="space-y-3">
                  {routines.length === 0 ? (
                    <div className="text-center text-sm text-slate-500">
                      Nenhuma rotina ainda
                    </div>
                  ) : (
                    routines.map((routine) => (
                      <div
                        key={routine.id}
                        className="rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-slate-900">{routine.name}</h4>
                            <p className="text-sm text-slate-600">{routine.description}</p>
                            <p className="text-xs text-slate-500">
                              Agendamento: {routine.schedule}
                            </p>
                          </div>
                          <button
                            onClick={() => handleRunRoutine(routine)}
                            className="rounded-lg bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-900 hover:bg-emerald-200"
                          >
                            ▶ Executar
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "memory" && (
                <div className="space-y-3">
                  {memories.length === 0 ? (
                    <div className="text-center text-sm text-slate-500">
                      Nenhuma memória ainda
                    </div>
                  ) : (
                    memories.map((memory) => (
                      <div
                        key={memory.id}
                        className="rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-slate-900">{memory.key}</h4>
                            <p className="text-sm text-slate-600">{memory.value}</p>
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {new Date(memory.created_at).toLocaleDateString("pt-BR")}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === "logs" && (
                <div className="space-y-2">
                  {logs.length === 0 ? (
                    <div className="text-center text-sm text-slate-500">
                      Nenhum log ainda
                    </div>
                  ) : (
                    logs.map((log) => (
                      <div
                        key={log.id}
                        className="rounded-xl bg-slate-50 px-4 py-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-900">
                            {log.action_type}
                          </span>
                          <span className="text-slate-500">
                            {new Date(log.created_at).toLocaleString("pt-BR")}
                          </span>
                        </div>
                        <div className="mt-1 text-slate-600">{log.description}</div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
