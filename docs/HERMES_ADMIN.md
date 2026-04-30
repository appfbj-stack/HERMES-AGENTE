# Hermes Admin

## Visão geral

O Hermes Admin é o assistente interno do painel `Admin Master`. Ele roda dentro do projeto atual e usa as rotas já registradas em `/admin/hermes/*`.

O objetivo dele é ajudar o `super_admin` com:

- status do sistema
- listagem de módulos
- análise do projeto
- leitura de erros
- tarefas, projetos, rotinas, memória e logs administrativos

## Escopo atual

O que existe hoje no sistema:

- backend FastAPI com rotas `POST /admin/hermes/chat` e endpoints administrativos auxiliares
- integração do painel web com o fluxo de Hermes Admin
- integração do bot Telegram admin com o mesmo contexto `super_admin`
- proteção por `is_super_admin = true`
- registro de ações administrativas em log

O que não deve ser assumido:

- não existe backend separado do Hermes Admin
- não existe banco separado
- não existe fluxo liberado para tenants/clientes comuns

## Rotas principais

- `POST /admin/hermes/chat`
- `GET /admin/hermes/dashboard`
- `GET /admin/hermes/tasks`
- `GET /admin/hermes/projects`
- `GET /admin/hermes/routines`
- `GET /admin/hermes/memory`
- `GET /admin/hermes/logs`

## Acesso

Requisitos:

- usuário autenticado
- `is_super_admin = true`

Usuários comuns e tenants clientes não devem acessar esse módulo.

## Painel web

No frontend, o chat do painel usa o fluxo Hermes Admin quando o usuário autenticado é `super_admin`.

Com isso:

- `super_admin` usa o chat administrativo
- usuário comum continua no chat padrão do tenant

## Telegram admin

O bot admin usa o webhook dedicado:

- `/webhook/telegram-admin`

Ele responde com contexto global de administração e não deve reutilizar o comportamento de cliente/tenant comum.

## Comandos esperados

Exemplos de uso já suportados no fluxo admin:

- `status do sistema`
- `listar módulos`
- `ver erros`
- `analisar projeto`
- `o que falta fazer`

## Observações de operação

- logs do Hermes Admin e dos serviços de suporte devem sair pelo logger central do backend
- erros de integração externa devem ser observados no backend/Coolify
- qualquer ajuste novo deve preservar isolamento por tenant nas áreas não administrativas

## Teste rápido

1. Entrar no painel com usuário `super_admin`.
2. Abrir `/chat`.
3. Enviar `status do sistema`.
4. Confirmar resposta administrativa.
5. Testar o bot Telegram admin com `listar módulos`.

## Deploy

Ver também:

- [README.md](../README.md)
- [DEPLOY.md](./DEPLOY.md)
