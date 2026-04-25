import { useEffect, useState } from 'react'
import api from '../api/client'

interface Stats {
  credits: number
  chats: number
  leads: number
  tasks: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({ credits: 0, chats: 0, leads: 0, tasks: 0 })
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get('/api/credits'),
      api.get('/api/chats'),
      api.get('/api/leads'),
      api.get('/api/tasks'),
    ])
      .then(([c, ch, l, t]) => {
        setStats({
          credits: c.data.balance,
          chats: ch.data.length,
          leads: l.data.length,
          tasks: t.data.length,
        })
      })
      .catch(() => setError('Backend offline. Mostrando zerado.'))
  }, [])

  const Card = ({ title, value }: { title: string; value: number }) => (
    <div className="bg-white rounded-2xl shadow p-6">
      <div className="text-sm text-wa-subtext">{title}</div>
      <div className="text-3xl font-bold text-wa-greenDark mt-1">{value}</div>
    </div>
  )

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      {error && <p className="mb-4 text-amber-700 text-sm">{error}</p>}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card title="Créditos" value={stats.credits} />
        <Card title="Conversas" value={stats.chats} />
        <Card title="Leads" value={stats.leads} />
        <Card title="Tarefas" value={stats.tasks} />
      </div>
    </div>
  )
}
