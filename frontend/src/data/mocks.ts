import type { Conversation, ChatMessage } from '../types'

export const mockConversations: Conversation[] = [
  {
    id: '1',
    name: 'João Silva',
    phone: '(15) 99999-0000',
    lastMessage: 'Posso agendar uma visita amanhã?',
    lastMessageAt: new Date(Date.now() - 2 * 60_000).toISOString(),
    status: 'ai',
    online: true,
    unread: 2,
  },
  {
    id: '2',
    name: 'Maria Souza',
    phone: '(11) 98888-1234',
    lastMessage: 'Obrigada pelo atendimento!',
    lastMessageAt: new Date(Date.now() - 25 * 60_000).toISOString(),
    status: 'human',
    online: false,
    unread: 0,
  },
  {
    id: '3',
    name: 'Carlos Mendes',
    phone: '(21) 97777-5555',
    lastMessage: 'Vou pensar e te respondo.',
    lastMessageAt: new Date(Date.now() - 3 * 60 * 60_000).toISOString(),
    status: 'paused',
    online: true,
    unread: 0,
  },
  {
    id: '4',
    name: 'Ana Paula',
    phone: '(31) 96666-7777',
    lastMessage: 'Quero saber sobre os planos.',
    lastMessageAt: new Date(Date.now() - 24 * 60 * 60_000).toISOString(),
    status: 'ai',
    online: false,
    unread: 1,
  },
  {
    id: '5',
    name: 'Pedro Lima',
    phone: '(85) 95555-3232',
    lastMessage: 'Fechado, pode mandar a proposta.',
    lastMessageAt: new Date(Date.now() - 2 * 24 * 60 * 60_000).toISOString(),
    status: 'closed',
    online: false,
    unread: 0,
  },
]

export const mockMessages: Record<string, ChatMessage[]> = {
  '1': [
    {
      id: 'm1',
      conversationId: '1',
      sender_type: 'user',
      content: 'Oi, queria saber sobre os planos.',
      created_at: new Date(Date.now() - 30 * 60_000).toISOString(),
    },
    {
      id: 'm2',
      conversationId: '1',
      sender_type: 'assistant',
      content:
        'Olá, João! Temos 3 planos: Starter, Pro e Enterprise. Qual encaixa melhor com o seu uso?',
      created_at: new Date(Date.now() - 28 * 60_000).toISOString(),
    },
    {
      id: 'm3',
      conversationId: '1',
      sender_type: 'user',
      content: 'O Pro. Posso agendar uma visita amanhã?',
      created_at: new Date(Date.now() - 2 * 60_000).toISOString(),
    },
  ],
  '2': [
    {
      id: 'm4',
      conversationId: '2',
      sender_type: 'user',
      content: 'Tudo bem? Preciso de ajuda com integração.',
      created_at: new Date(Date.now() - 90 * 60_000).toISOString(),
    },
    {
      id: 'm5',
      conversationId: '2',
      sender_type: 'human',
      content: 'Aqui é o Fernando, posso te ajudar agora.',
      created_at: new Date(Date.now() - 80 * 60_000).toISOString(),
    },
    {
      id: 'm6',
      conversationId: '2',
      sender_type: 'user',
      content: 'Obrigada pelo atendimento!',
      created_at: new Date(Date.now() - 25 * 60_000).toISOString(),
    },
  ],
  '3': [
    {
      id: 'm7',
      conversationId: '3',
      sender_type: 'user',
      content: 'Você tem desconto à vista?',
      created_at: new Date(Date.now() - 5 * 60 * 60_000).toISOString(),
    },
    {
      id: 'm8',
      conversationId: '3',
      sender_type: 'assistant',
      content: 'Sim! 10% no PIX. Posso te mandar o link?',
      created_at: new Date(Date.now() - 4 * 60 * 60_000).toISOString(),
    },
    {
      id: 'm9',
      conversationId: '3',
      sender_type: 'user',
      content: 'Vou pensar e te respondo.',
      created_at: new Date(Date.now() - 3 * 60 * 60_000).toISOString(),
    },
  ],
  '4': [
    {
      id: 'm10',
      conversationId: '4',
      sender_type: 'user',
      content: 'Quero saber sobre os planos.',
      created_at: new Date(Date.now() - 24 * 60 * 60_000).toISOString(),
    },
  ],
  '5': [
    {
      id: 'm11',
      conversationId: '5',
      sender_type: 'user',
      content: 'Fechado, pode mandar a proposta.',
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60_000).toISOString(),
    },
  ],
}
