import { useMemo, useState } from 'react'
import clsx from 'clsx'
import { Search, Plus } from 'lucide-react'
import type { Conversation } from '../../types'

interface Props {
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew?: () => void
}

const STATUS_DOT: Record<Conversation['status'], string> = {
  ai: 'bg-wa-green',
  human: 'bg-amber-500',
  paused: 'bg-gray-400',
  closed: 'bg-red-500',
}

const STATUS_TEXT: Record<Conversation['status'], string> = {
  ai: 'IA',
  human: 'Humano',
  paused: 'Pausada',
  closed: 'Encerrada',
}

function formatRelative(iso: string) {
  const d = new Date(iso)
  const today = new Date()
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) return 'Ontem'
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

export default function ConversationList({ conversations, activeId, onSelect, onNew }: Props) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return conversations
    return conversations.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.phone.toLowerCase().includes(q) ||
        c.lastMessage.toLowerCase().includes(q),
    )
  }, [query, conversations])

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="p-3 border-b border-wa-border flex items-center gap-2">
        <span className="font-semibold text-wa-text flex-1">Conversas</span>
        {onNew && (
          <button
            onClick={onNew}
            className="p-2 rounded-full bg-wa-green text-white hover:bg-wa-greenDark"
            title="Nova mensagem"
          >
            <Plus size={16} />
          </button>
        )}
      </div>

      <div className="px-3 py-2 border-b border-wa-border">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-wa-bg rounded-lg">
          <Search size={16} className="text-wa-subtext" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar conversa"
            className="flex-1 bg-transparent outline-none text-sm"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="p-6 text-center text-sm text-wa-subtext">
            Nenhuma conversa encontrada.
          </div>
        )}
        {filtered.map((c) => {
          const initials = c.name
            .split(' ')
            .map((n) => n[0])
            .slice(0, 2)
            .join('')
            .toUpperCase()

          return (
            <button
              key={c.id}
              onClick={() => onSelect(c.id)}
              className={clsx(
                'w-full text-left px-3 py-3 border-b border-wa-border flex gap-3 hover:bg-wa-bg transition',
                activeId === c.id && 'bg-wa-bg',
              )}
            >
              <div className="relative shrink-0">
                <div className="w-12 h-12 rounded-full bg-wa-green text-white flex items-center justify-center font-semibold">
                  {initials || '?'}
                </div>
                {c.online && (
                  <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-wa-green border-2 border-white" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-wa-text truncate">{c.name}</div>
                  <div className="text-[11px] text-wa-subtext shrink-0 ml-2">
                    {formatRelative(c.lastMessageAt)}
                  </div>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs text-wa-subtext truncate flex-1">
                    {c.lastMessage}
                  </div>
                  {c.unread > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center min-w-[20px] h-5 text-[11px] font-semibold text-white bg-wa-green rounded-full px-1.5">
                      {c.unread}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 mt-0.5">
                  <span className={clsx('w-1.5 h-1.5 rounded-full', STATUS_DOT[c.status])} />
                  <span className="text-[10px] uppercase tracking-wide text-wa-subtext">
                    {STATUS_TEXT[c.status]}
                  </span>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
