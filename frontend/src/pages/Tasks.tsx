import { FormEvent, useEffect, useState } from 'react'
import api from '../api/client'

interface Task {
  id: number
  title: string
  description?: string
  status: string
  due_at?: string | null
  created_at: string
}

const STATUS = ['pending', 'in_progress', 'done'] as const

export default function Tasks() {
  const [items, setItems] = useState<Task[]>([])
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')

  async function load() {
    try {
      const { data } = await api.get<Task[]>('/api/tasks')
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
    if (!title.trim()) return
    await api.post('/api/tasks', { title })
    setTitle('')
    load()
  }

  async function setStatus(id: number, status: string) {
    await api.patch(`/api/tasks/${id}`, { title: items.find((t) => t.id === id)!.title, status })
    load()
  }

  async function remove(id: number) {
    await api.delete(`/api/tasks/${id}`)
    load()
  }

  return (
    <div className="p-6 md:p-8 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold mb-4">Tarefas</h1>
      {error && <p className="mb-3 text-amber-700 text-sm">{error}</p>}

      <form onSubmit={add} className="flex gap-2 bg-white p-3 rounded-xl shadow mb-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Nova tarefa"
          className="border rounded-lg px-3 py-2 flex-1"
        />
        <button className="bg-wa-green text-white px-4 py-2 rounded-lg hover:bg-wa-greenDark">
          Adicionar
        </button>
      </form>

      <div className="bg-white rounded-xl shadow divide-y">
        {items.length === 0 && (
          <div className="px-3 py-6 text-center text-wa-subtext">Nenhuma tarefa.</div>
        )}
        {items.map((t) => (
          <div key={t.id} className="flex items-center gap-2 px-3 py-2">
            <select
              value={t.status}
              onChange={(e) => setStatus(t.id, e.target.value)}
              className="border rounded-lg px-2 py-1 text-xs"
            >
              {STATUS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <span className="flex-1">{t.title}</span>
            <button onClick={() => remove(t.id)} className="text-red-600 text-sm hover:underline">
              excluir
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
