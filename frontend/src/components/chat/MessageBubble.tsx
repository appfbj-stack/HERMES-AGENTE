import clsx from 'clsx'
import type { ChatMessage } from '../../types'

interface Props {
  message: ChatMessage
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.sender_type === 'user'
  const isHuman = message.sender_type === 'human'

  return (
    <div className={clsx('flex w-full', isUser ? 'justify-start' : 'justify-end')}>
      <div
        className={clsx(
          'max-w-[78%] md:max-w-[60%] px-3 py-2 rounded-lg shadow-sm text-sm whitespace-pre-wrap break-words',
          isUser
            ? 'bg-wa-bubbleIn text-wa-text rounded-tl-sm'
            : isHuman
              ? 'bg-wa-bubbleHuman text-wa-text rounded-tr-sm'
              : 'bg-wa-bubbleOut text-wa-text rounded-tr-sm',
        )}
      >
        {!isUser && (
          <div className="text-[10px] uppercase tracking-wide text-wa-subtext mb-0.5">
            {isHuman ? 'Atendente' : 'IA'}
          </div>
        )}
        <div>{message.content}</div>
        <div className="text-[10px] text-wa-subtext mt-1 text-right">
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  )
}
