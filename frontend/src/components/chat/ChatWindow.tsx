import { useEffect, useRef } from 'react'
import type { ChatMessage, Conversation } from '../../types'
import ChatHeader from './ChatHeader'
import MessageBubble from './MessageBubble'
import MessageInput from './MessageInput'

interface Props {
  conversation: Conversation
  messages: ChatMessage[]
  onBack?: () => void
  onSend: (text: string) => void
  onAssumeHuman: () => void
  onTogglePauseAi: () => void
  onCreateLead: () => void
  onCreateTask: () => void
  onShowHistory: () => void
}

export default function ChatWindow({
  conversation,
  messages,
  onBack,
  onSend,
  onAssumeHuman,
  onTogglePauseAi,
  onCreateLead,
  onCreateTask,
  onShowHistory,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const isPaused = conversation.status === 'paused'
  const isClosed = conversation.status === 'closed'

  return (
    <div className="flex flex-col h-full bg-wa-chatbg">
      <ChatHeader
        conversation={conversation}
        onBack={onBack}
        onAssumeHuman={onAssumeHuman}
        onTogglePauseAi={onTogglePauseAi}
        onCreateLead={onCreateLead}
        onCreateTask={onCreateTask}
        onShowHistory={onShowHistory}
      />

      <div className="flex-1 overflow-y-auto p-3 md:p-6 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-sm text-wa-subtext py-12">
            Sem mensagens ainda. Inicie a conversa abaixo.
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        <div ref={bottomRef} />
      </div>

      <MessageInput onSend={onSend} disabled={isPaused || isClosed} />
    </div>
  )
}
