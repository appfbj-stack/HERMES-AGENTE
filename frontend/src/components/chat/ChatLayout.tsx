import { useEffect, useState } from 'react'
import clsx from 'clsx'
import ConversationList from './ConversationList'
import ChatWindow from './ChatWindow'
import { mockConversations, mockMessages } from '../../data/mocks'
import type { ChatMessage, Conversation } from '../../types'

export default function ChatLayout() {
  const [conversations, setConversations] = useState<Conversation[]>(mockConversations)
  const [messagesById, setMessagesById] = useState<Record<string, ChatMessage[]>>(mockMessages)
  const [activeId, setActiveId] = useState<string | null>(mockConversations[0]?.id ?? null)
  const [showListMobile, setShowListMobile] = useState(true)

  const active = conversations.find((c) => c.id === activeId) ?? null
  const messages = active ? messagesById[active.id] ?? [] : []

  useEffect(() => {
    if (activeId) setShowListMobile(false)
  }, [activeId])

  function updateConversation(id: string, patch: Partial<Conversation>) {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    )
  }

  function appendMessage(convId: string, msg: ChatMessage) {
    setMessagesById((prev) => ({
      ...prev,
      [convId]: [...(prev[convId] ?? []), msg],
    }))
    updateConversation(convId, {
      lastMessage: msg.content,
      lastMessageAt: msg.created_at,
    })
  }

  function handleSend(text: string) {
    if (!active) return
    const userMsg: ChatMessage = {
      id: 'u-' + Date.now(),
      conversationId: active.id,
      sender_type: active.status === 'human' ? 'human' : 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    appendMessage(active.id, userMsg)

    if (active.status === 'ai') {
      setTimeout(() => {
        const reply: ChatMessage = {
          id: 'a-' + Date.now(),
          conversationId: active.id,
          sender_type: 'assistant',
          content: 'Recebi! (resposta mock — aqui virá o DeepSeek)',
          created_at: new Date().toISOString(),
        }
        appendMessage(active.id, reply)
      }, 600)
    }
  }

  function handleNewChat() {
    const id = 'new-' + Date.now()
    const conv: Conversation = {
      id,
      name: 'Nova conversa',
      phone: '',
      lastMessage: '',
      lastMessageAt: new Date().toISOString(),
      status: 'ai',
      online: false,
      unread: 0,
    }
    setConversations((prev) => [conv, ...prev])
    setMessagesById((prev) => ({ ...prev, [id]: [] }))
    setActiveId(id)
  }

  return (
    <div className="flex h-full">
      <div
        className={clsx(
          'w-full md:w-96 md:border-r md:border-wa-border',
          !showListMobile && 'hidden md:block',
        )}
      >
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={handleNewChat}
        />
      </div>

      <div
        className={clsx(
          'flex-1',
          showListMobile && 'hidden md:block',
        )}
      >
        {active ? (
          <ChatWindow
            conversation={active}
            messages={messages}
            onBack={() => setShowListMobile(true)}
            onSend={handleSend}
            onAssumeHuman={() => updateConversation(active.id, { status: 'human' })}
            onTogglePauseAi={() =>
              updateConversation(active.id, {
                status: active.status === 'paused' ? 'ai' : 'paused',
              })
            }
            onCreateLead={() =>
              alert(`Lead criado para ${active.name} (${active.phone})`)
            }
            onCreateTask={() =>
              alert(`Tarefa criada relacionada a ${active.name}`)
            }
            onShowHistory={() =>
              alert(`Histórico de ${active.name} (${messages.length} mensagens)`)
            }
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-wa-chatbg text-wa-subtext text-sm">
            Selecione uma conversa para começar
          </div>
        )}
      </div>
    </div>
  )
}
