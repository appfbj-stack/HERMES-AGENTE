export type SenderType = 'user' | 'assistant' | 'human'
export type ConversationStatus = 'ai' | 'human' | 'paused' | 'closed'

export interface Conversation {
  id: string
  name: string
  phone: string
  lastMessage: string
  lastMessageAt: string
  status: ConversationStatus
  online: boolean
  unread: number
  avatar?: string
}

export interface ChatMessage {
  id: string
  conversationId: string
  sender_type: SenderType
  content: string
  created_at: string
}

export interface AuthUser {
  id: number
  name: string
  email: string
  tenantId: number
}
