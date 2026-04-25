import { useEffect, useState } from 'react'
import api from '../api/client'

interface UsageLog {
  id: number
  model: string
  tokens_in: number
  tokens_out: number
  cost_credits: number
  created_at: string
}

export default function Credits() {
  const [balance, setBalance] = useState(0)
  const [logs, setLogs] = useState<UsageLog[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.get('/api/credits'), api.get('/api/credits/usage')])
      .then(([c, u]) => {
        setBalance(c.data.balance)
        setLogs(u.data.recent_logs)
      })
      .catch(() => setError('Backend offline.'))
  }, [])

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-4">Créditos</h1>
      {error && <p className="mb-3 text-amber-700 text-sm">{error}</p>}

      <div className="bg-white rounded-2xl shadow p-6 mb-6">
        <div className="text-sm text-wa-subtext">Saldo atual</div>
        <div className="text-4xl font-bold text-wa-greenDark">{balance}</div>
      </div>

      <h2 className="font-semibold mb-2">Uso recente</h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-wa-bg text-wa-subtext">
            <tr>
              <th className="text-left px-3 py-2">Modelo</th>
              <th className="text-right px-3 py-2">Tokens in</th>
              <th className="text-right px-3 py-2">Tokens out</th>
              <th className="text-right px-3 py-2">Custo</th>
              <th className="text-left px-3 py-2">Data</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-wa-subtext">
                  Sem uso registrado.
                </td>
              </tr>
            )}
            {logs.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="px-3 py-2">{l.model}</td>
                <td className="px-3 py-2 text-right">{l.tokens_in}</td>
                <td className="px-3 py-2 text-right">{l.tokens_out}</td>
                <td className="px-3 py-2 text-right">{l.cost_credits}</td>
                <td className="px-3 py-2">
                  {new Date(l.created_at).toLocaleString('pt-BR')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
