import clsx from 'clsx'
import { ArrowLeft, History, UserPlus, Pause, Play, ListPlus, Hand } from 'lucide-react'
import type { Conversation } from '../../types'

interface Props {
  conversation: Conversation
  onBack?: () => void
  onAssumeHuman: () => void
  onTogglePauseAi: () => void
  onCreateLead: () => void
  onCreateTask: () => void
  onShowHistory: () => void
}

const STATUS_LABELS: Record<Conversation['status'], string> = {
  ai: 'IA atendendo',
  human: 'Humano atendendo',
  paused: 'IA pausada',
  closed: 'Encerrada',
}

const STATUS_COLOR: Record<Conversation['status'], string> = {
  ai: 'bg-wa-green',
  human: 'bg-amber-500',
  paused: 'bg-gray-400',
  closed: 'bg-red-500',
}

export default function ChatHeader({
  conversation,
  onBack,
  onAssumeHuman,
  onTogglePauseAi,
  onCreateLead,
  onCreateTask,
  onShowHistory,
}: Props) {
  const initials = conversation.name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
  const isPaused = conversation.status === 'paused'

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-white border-b border-wa-border">
      {onBack && (
        <button
          onClick={onBack}
          className="md:hidden p-1 text-wa-text"
          title="Voltar"
        >
          <ArrowLeft size={20} />
        </button>
      )}
      <div className="relative">
        <div className="w-10 h-10 rounded-full bg-wa-green text-white flex items-center justify-center font-semibold">
          {initials || '?'}
        </div>
        {conversation.online && (
          <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-wa-green border-2 border-white" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-wa-text truncate">{conversation.name}</div>
        <div className="text-xs text-wa-subtext flex items-center gap-2">
          <span className="truncate">{conversation.phone}</span>
          <span className="flex items-center gap-1">
            <span
              className={clsx('w-1.5 h-1.5 rounded-full', STATUS_COLOR[conversation.status])}
            />
            {STATUS_LABELS[conversation.status]}
          </span>
        </div>
      </div>

      <div className="hidden sm:flex items-center gap-1">
        <button
          onClick={onAssumeHuman}
          className="px-3 py-1.5 text-xs rounded-full bg-amber-500 text-white hover:bg-amber-600 flex items-center gap-1"
          title="Assumir atendimento"
        >
          <Hand size={14} /> Assumir
        </button>
        <button
          onClick={onTogglePauseAi}
          className="px-3 py-1.5 text-xs rounded-full bg-wa-bg text-wa-text hover:bg-wa-border flex items-center gap-1"
          title={isPaused ? 'Retomar IA' : 'Pausar IA'}
        >
          {isPaused ? <Play size={14} /> : <Pause size={14} />}
          {isPaused ? 'Retomar IA' : 'Pausar IA'}
        </button>
        <button
          onClick={onCreateLead}
          className="px-3 py-1.5 text-xs rounded-full bg-wa-bg text-wa-text hover:bg-wa-border flex items-center gap-1"
          title="Criar lead"
        >
          <UserPlus size={14} /> Lead
        </button>
        <button
          onClick={onCreateTask}
          className="px-3 py-1.5 text-xs rounded-full bg-wa-bg text-wa-text hover:bg-wa-border flex items-center gap-1"
          title="Criar tarefa"
        >
          <ListPlus size={14} /> Tarefa
        </button>
        <button
          onClick={onShowHistory}
          className="px-3 py-1.5 text-xs rounded-full bg-wa-bg text-wa-text hover:bg-wa-border flex items-center gap-1"
          title="Ver histórico"
        >
          <History size={14} /> Histórico
        </button>
      </div>

      {/* Mobile: action menu collapsed */}
      <div className="sm:hidden flex gap-1">
        <button
          onClick={onAssumeHuman}
          className="p-2 rounded-full bg-amber-500 text-white"
          title="Assumir"
        >
          <Hand size={16} />
        </button>
        <button
          onClick={onTogglePauseAi}
          className="p-2 rounded-full bg-wa-bg text-wa-text"
          title="Pausar IA"
        >
          {isPaused ? <Play size={16} /> : <Pause size={16} />}
        </button>
      </div>
    </div>
  )
}
