import { useAuth } from '../contexts/AuthContext'

export default function Settings() {
  const { user } = useAuth()

  const Field = ({ label, value }: { label: string; value: string | number }) => (
    <div>
      <div className="text-xs text-wa-subtext">{label}</div>
      <div className="text-sm font-medium text-wa-text">{value}</div>
    </div>
  )

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-4">Configurações</h1>

      <section className="bg-white rounded-2xl shadow p-6 space-y-3 mb-6">
        <h2 className="font-semibold">Conta</h2>
        <Field label="Nome" value={user?.name ?? '—'} />
        <Field label="Email" value={user?.email ?? '—'} />
        <Field label="Tenant ID" value={user?.tenantId ?? '—'} />
      </section>

      <section className="bg-white rounded-2xl shadow p-6 space-y-3">
        <h2 className="font-semibold">Integrações</h2>
        <p className="text-sm text-wa-subtext">
          As chaves de DeepSeek, Telegram e WhatsApp são configuradas no
          arquivo <code className="bg-wa-bg px-1 rounded">.env</code> do backend.
          Para apontar este frontend a um backend remoto, defina{' '}
          <code className="bg-wa-bg px-1 rounded">VITE_API_URL</code>.
        </p>
      </section>
    </div>
  )
}
