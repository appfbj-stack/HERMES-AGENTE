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
  updateAdminTenant,
} from "./api";
import { NICHE_TEMPLATES } from "./niches";
import type { AdminTenant, NicheTemplate } from "./types";

function genPassword(): string {
  return "Hermes" + Math.floor(1000 + Math.random() * 9000) + "!";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("pt-BR");
}

function pct(t: AdminTenant): number {
  if (!t.credits_total) return 0;
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [qrTenant, setQrTenant] = useState<AdminTenant | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await getAdminTenants();
      setTenants(data);
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
  const totalUsedMessages = tenants.reduce((acc, t) => acc + t.credits_used, 0);
  const blocked = tenants.filter((t) => t.credits_remaining <= 0).length;

  return (
    <div className="space-y-6">
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
                          {t.credits_remaining.toLocaleString("pt-BR")} /{" "}
                          {t.credits_total.toLocaleString("pt-BR")}
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
                      <td className="px-3 py-3">
                        {!t.active ? (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] uppercase text-red-700">
                            Inativo
                          </span>
                        ) : t.credits_remaining <= 0 ? (
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

      {qrTenant && <QRCodeModal tenant={qrTenant} onClose={() => setQrTenant(null)} />}
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
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-xs font-semibold uppercase text-slate-500 mb-2">🤖 Bot do Telegram (opcional)</div>
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  className="input"
                  placeholder="Token (do @BotFather)"
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
              <p className="mt-2 text-xs text-slate-500">
                Você pode deixar em branco e configurar depois nas configurações do tenant.
              </p>
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
              <p className="text-sm text-emerald-900">
                Manda essas informações pro cliente:
              </p>
              <div className="mt-3 space-y-2 rounded-xl bg-white p-4 font-mono text-sm">
                <div>🌐 Painel: https://meuchat.fbautomacao.space</div>
                <div>📧 Login: {form.user_email}</div>
                <div>🔑 Senha: {form.user_password}</div>
                {form.telegram_bot_username && (
                  <div>
                    🤖 Bot: https://t.me/{form.telegram_bot_username.replace("@", "")}
                  </div>
                )}
              </div>
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

function QRCodeModal({ tenant, onClose }: { tenant: AdminTenant; onClose: () => void }) {
  const username = (tenant.telegram_bot_username || "").replace("@", "");
  const link = username ? `https://t.me/${username}` : "";
  const qrUrl = link
    ? `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(link)}`
    : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-[32px] bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-serif text-2xl">QR Code — {tenant.name}</h2>
          <button onClick={onClose} className="text-2xl text-slate-400 hover:text-slate-600">
            ×
          </button>
        </div>
        {!username ? (
          <div className="rounded-2xl bg-amber-50 p-5 text-sm text-amber-800">
            ⚠️ Esse cliente ainda não tem bot configurado. Edite o tenant e adicione um username.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center rounded-2xl bg-slate-50 p-6">
              <img src={qrUrl} alt="QR Code" className="h-64 w-64" />
            </div>
            <div className="space-y-2 rounded-xl bg-emerald-50 p-4 text-sm">
              <div className="font-semibold">Link do bot:</div>
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
                Copiar link
              </button>
              <a
                href={qrUrl}
                download={`qrcode-${username}.png`}
                className="flex-1 rounded-2xl bg-emerald-600 px-5 py-2 text-center text-sm font-semibold text-white hover:bg-emerald-700"
              >
                Baixar QR
              </a>
            </div>
            <p className="text-xs text-slate-500">
              Envie esse QR pro cliente colocar no Insta, vitrine, cardápio, e-mail, etc. Quem
              escanear abre o bot direto no Telegram.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
