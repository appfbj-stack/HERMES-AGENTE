import { FormEvent, useEffect, useState } from 'react'
import api from '../api/client'

interface Lead {
  id: number
  name: string
  email?: string
  phone?: string
  status: string
  notes?: string
  created_at: string
}

export default function Leads() {
  const [items, setItems] = useState<Lead[]>([])
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  async function load() {
    try {
      const { data } = await api.get<Lead[]>('/api/leads')
      setItems(data)
    } catch {
      setError('Backend offline.')
    }
  }
  useEffect(() => {
    load()
  }, [])

  async function add(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    await api.post('/api/leads', { name, phone, email })
    setName('')
    setPhone('')
    setEmail('')
    load()
  }

  async function remove(id: number) {
    await api.delete(`/api/leads/${id}`)
    load()
  }

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-4">Leads</h1>
      {error && <p className="mb-3 text-amber-700 text-sm">{error}</p>}

      <form onSubmit={add} className="flex flex-wrap gap-2 bg-white p-3 rounded-xl shadow mb-4">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nome"
          className="border rounded-lg px-3 py-2 flex-1 min-w-[160px]"
        />
        <input
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="Telefone"
          className="border rounded-lg px-3 py-2 flex-1 min-w-[140px]"
        />
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="border rounded-lg px-3 py-2 flex-1 min-w-[160px]"
        />
        <button className="bg-wa-green text-white px-4 py-2 rounded-lg hover:bg-wa-greenDark">
          Adicionar
        </button>
      </form>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-wa-bg text-wa-subtext">
            <tr>
              <th className="text-left px-3 py-2">Nome</th>
              <th className="text-left px-3 py-2">Telefone</th>
              <th className="text-left px-3 py-2">Email</th>
              <th className="text-left px-3 py-2">Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-wa-subtext">
                  Nenhum lead.
                </td>
              </tr>
            )}
            {items.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="px-3 py-2">{l.name}</td>
                <td className="px-3 py-2">{l.phone || '—'}</td>
                <td className="px-3 py-2">{l.email || '—'}</td>
                <td className="px-3 py-2">{l.status}</td>
                <td className="px-3 py-2 text-right">
                  <button onClick={() => remove(l.id)} className="text-red-600 hover:underline">
                    excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
