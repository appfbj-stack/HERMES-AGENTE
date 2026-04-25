# PRD

Versão operacional do PRD enviado para este repositório.

## Objetivo

Construir uma plataforma SaaS multi-tenant que:

- receba mensagens via Telegram
- responda com DeepSeek
- mantenha histórico por tenant
- converta conversas em leads
- permita operação humana no painel
- controle consumo por créditos

## Entregável atual

- backend FastAPI multi-tenant com JWT
- modelos principais do SaaS
- webhook Telegram com fluxo de créditos
- integração por provedor de IA configurável, com Hermes como padrão
- painel React com layout de chat estilo WhatsApp
- Dockerfiles, compose e documentação de deploy

## Limites desta primeira entrega

- sem fila assíncrona dedicada
- sem integração de pagamento
- sem upload de mídia
- sem websocket em tempo real
- sem migrações Alembic

## Próximas evoluções

- websocket ou SSE para chat em tempo real
- onboarding self-service de tenants
- billing e planos
- WhatsApp e Chatwoot
- automações avançadas por agente
