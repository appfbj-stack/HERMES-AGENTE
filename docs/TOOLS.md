# Módulo Tools/Skills - Documentação

## Visão Geral

O módulo Tools fornece ferramentas reutilizáveis para automação no sistema HERMES AGENTE. As ferramentas são integradas ao backend existente, seguindo os padrões de multi-tenancy e autenticação.

## Configuração

### Variáveis de Ambiente (.env)

```env
# Coolify (deploy)
COOLIFY_API_BASE_URL=https://your-coolify-instance.com
COOLIFY_API_KEY=your-coolify-api-key

# GitHub
GITHUB_TOKEN=ghp_your_github_token
GITHUB_OWNER=your-github-username
GITHUB_REPO=your-repo-name

# Social files
SOCIAL_FILES_PATH=./social
```

### Instalação de Dependências

As novas dependências já estão no `requirements.txt`:
- `GitPython==3.1.43` - Operações Git
- `schedule==1.1.0` - Agendamento de rotinas
- `aiofiles==24.1.0` - I/O assíncrono de arquivos

Para instalar:
```bash
cd backend
pip install -r requirements.txt
```

### Migration

Execute a migration SQL:
```bash
psql "$DATABASE_URL" -f backend/migrations/002_tools_module.sql
```

Ou via Docker Compose:
```bash
docker compose exec db psql -U postgres -d hermes -f /app/migrations/002_tools_module.sql
```

## Rotas Disponíveis

Todas as rotas exigem autenticação via JWT (`Bearer token`).

Prefixo base: `/api/tools`

### GitHub

#### POST `/tools/github/commit`
Commit no repositório Git.

**Request:**
```json
{
  "message": "feat: add new feature",
  "files": ["file1.py", "file2.py"],
  "author_name": "Fernando",
  "author_email": "fernando@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "commit_hash": "abc123...",
  "message": "feat: add new feature",
  "author": "Fernando <fernando@example.com>"
}
```

#### POST `/tools/github/push`
Push para o repositório remoto.

**Request:**
```json
{
  "branch": "main"
}
```

**Response:**
```json
{
  "success": true,
  "branch": "main"
}
```

#### POST `/tools/github/pull-request`
Criar Pull Request no GitHub.

**Request:**
```json
{
  "title": "Add new feature",
  "body": "Description of changes",
  "head": "feature-branch",
  "base": "main"
}
```

**Response:**
```json
{
  "success": true,
  "pr": {...}
}
```

### Arquivos

#### GET `/tools/files/list`
Listar arquivos em um diretório.

**Query params:**
- `path` (string): Caminho do diretório (default: "./")
- `pattern` (string): Padrão de glob (opcional)

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "name": "file.py",
      "path": "src/file.py",
      "size": 1024,
      "modified": 1714320000
    }
  ],
  "total": 1
}
```

#### GET `/tools/files/read`
Ler conteúdo de um arquivo.

**Query params:**
- `path` (string): Caminho do arquivo
- `encoding` (string): Codificação (default: "utf-8")

**Response:**
```json
{
  "success": true,
  "content": "print('Hello World')",
  "size": 21
}
```

#### POST `/tools/files/write`
Escrever conteúdo em um arquivo.

**Request:**
```json
{
  "path": "./test.txt",
  "content": "Hello World",
  "encoding": "utf-8",
  "create_dirs": true
}
```

**Response:**
```json
{
  "success": true,
  "path": "./test.txt",
  "size": 11
}
```

#### POST `/tools/files/delete`
Deletar um arquivo.

**Request:**
```json
{
  "path": "./test.txt"
}
```

**Response:**
```json
{
  "success": true,
  "path": "./test.txt"
}
```

### Coolify

#### POST `/tools/coolify/deploy`
Disparar deploy no Coolify.

**Request:**
```json
{
  "application_id": "app-123",
  "branch": "main",
  "force_rebuild": false
}
```

**Response:**
```json
{
  "success": true,
  "deployment": {...}
}
```

#### POST `/tools/coolify/trigger`
Disparar webhook do Coolify.

**Request:**
```json
{
  "webhook_url": "https://coolify.example.com/webhook/abc",
  "payload": {
    "custom": "data"
  }
}
```

**Response:**
```json
{
  "success": true,
  "status": "triggered"
}
```

#### GET `/tools/coolify/status`
Obter status de uma aplicação no Coolify.

**Query params:**
- `application_id` (string): ID da aplicação

**Response:**
```json
{
  "success": true,
  "application": {...}
}
```

#### GET `/tools/coolify/deployments`
Listar deployments de uma aplicação.

**Query params:**
- `application_id` (string): ID da aplicação
- `limit` (int): Limite de resultados (default: 10)

**Response:**
```json
{
  "success": true,
  "deployments": [...]
}
```

### Social Files

#### GET `/tools/social/files`
Listar arquivos na pasta `/social`.

**Query params:**
- `pattern` (string): Padrão de glob (opcional)
- `subfolder` (string): Subpasta (opcional)

**Response:**
```json
{
  "success": true,
  "files": [...],
  "total": 5
}
```

#### GET `/tools/social/files/read`
Ler arquivo da pasta `/social`.

**Query params:**
- `filename` (string): Nome do arquivo
- `subfolder` (string): Subpasta (opcional)
- `encoding` (string): Codificação (default: "utf-8")

**Response:**
```json
{
  "success": true,
  "content": "...",
  "size": 1024
}
```

#### POST `/tools/social/files/write`
Escrever arquivo na pasta `/social`.

**Request:**
```json
{
  "filename": "post.txt",
  "content": "Hello social media",
  "subfolder": "instagram",
  "encoding": "utf-8"
}
```

**Response:**
```json
{
  "success": true,
  "path": "./social/instagram/post.txt",
  "size": 19
}
```

#### POST `/tools/social/files/delete`
Deletar arquivo da pasta `/social`.

**Request:**
```json
{
  "filename": "post.txt",
  "subfolder": "instagram"
}
```

**Response:**
```json
{
  "success": true,
  "path": "./social/instagram/post.txt"
}
```

### Rotinas

#### POST `/tools/routines/execute`
Executar uma rotina imediatamente.

**Request:**
```json
{
  "routine_name": "daily_report",
  "input_data": "{\"date\": \"2024-04-28\"}"
}
```

**Response:**
```json
{
  "success": true,
  "execution_id": 123,
  "result": "Routine executed with input: {...}"
}
```

#### POST `/tools/routines/schedule`
Agendar uma rotina recorrente.

**Request:**
```json
{
  "routine_name": "daily_report",
  "interval": "hours",
  "interval_value": 24
}
```

**Intervalos suportados:**
- `seconds`
- `minutes`
- `hours`
- `days`

**Response:**
```json
{
  "success": true,
  "job_id": "daily_report_1"
}
```

#### POST `/tools/routines/cancel`
Cancelar rotina agendada.

**Request:**
```json
{
  "job_id": "daily_report_1"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "daily_report_1"
}
```

#### GET `/tools/routines/scheduled`
Listar rotinas agendadas.

**Response:**
```json
{
  "success": true,
  "jobs": ["daily_report_1", "cleanup_1"]
}
```

### Execuções (Histórico)

#### GET `/tools/executions`
Listar histórico de execuções.

**Query params:**
- `limit` (int): Limite (default: 50)
- `offset` (int): Offset (default: 0)

**Response:**
```json
{
  "executions": [
    {
      "id": 1,
      "tenant_id": 1,
      "skill_name": "github_commit",
      "status": "completed",
      "input_data": "{\"message\": \"...\"}",
      "output_data": "{\"commit_hash\": \"...\"}",
      "error_message": null,
      "started_at": "2024-04-28T10:00:00Z",
      "completed_at": "2024-04-28T10:00:05Z",
      "created_at": "2024-04-28T10:00:00Z",
      "updated_at": "2024-04-28T10:00:05Z"
    }
  ],
  "total": 1
}
```

#### GET `/tools/executions/{execution_id}`
Obter detalhes de uma execução específica.

**Response:**
```json
{
  "id": 1,
  "tenant_id": 1,
  "skill_name": "github_commit",
  "status": "completed",
  ...
}
```

## Exemplos de Uso

### Fluxo: Commit e Push no GitHub

```bash
# 1. Fazer commit
curl -X POST http://localhost:8000/api/tools/github/commit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "feat: add new feature",
    "files": ["src/feature.py"]
  }'

# 2. Push
curl -X POST http://localhost:8000/api/tools/github/push \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"branch": "main"}'
```

### Fluxo: Deploy no Coolify

```bash
# Disparar deploy
curl -X POST http://localhost:8000/api/tools/coolify/deploy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "app-123",
    "branch": "main"
  }'

# Verificar status
curl -X GET "http://localhost:8000/api/tools/coolify/status?application_id=app-123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Fluxo: Gerenciar Arquivos /social

```bash
# Listar arquivos
curl -X GET "http://localhost:8000/api/tools/social/files?subfolder=instagram" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Ler arquivo
curl -X GET "http://localhost:8000/api/tools/social/files/read?filename=post.txt&subfolder=instagram" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Escrever arquivo
curl -X POST http://localhost:8000/api/tools/social/files/write \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "post.txt",
    "content": "Hello Instagram!",
    "subfolder": "instagram"
  }'
```

## Segurança

- Todas as rotas exigem autenticação JWT
- Dados isolados por `tenant_id`
- Logs de execução em `skill_executions`
- Validação de inputs via Pydantic

## Arquitetura

```
backend/app/
├── routes/tools.py         # Endpoints das ferramentas
├── services/
│   ├── github.py          # Integração GitHub
│   ├── file_reader.py     # Leitura/escrita de arquivos
│   ├── coolify.py         # Deploy via Coolify API
│   ├── social_reader.py   # Leitura da pasta /social
│   └── scheduler.py       # Agendamento de rotinas
├── models.py              # Modelo SkillExecution
└── schemas.py             # Pydantic schemas
```

## Troubleshooting

### GitHub Token Invalid
Erro: "GitHub token not configured"
**Solução:** Configure `GITHUB_TOKEN` no `.env`

### Coolify API Key Invalid
Erro: "Coolify API key not configured"
**Solução:** Configure `COOLIFY_API_BASE_URL` e `COOLIFY_API_KEY` no `.env`

### Social Folder Not Found
Erro: "File does not exist"
**Solução:** Configure `SOCIAL_FILES_PATH` no `.env` ou crie a pasta manualmente

### Scheduler Not Running
As rotinas agendadas não estão executando
**Solução:** O scheduler é iniciado automaticamente na primeira agendagem. Verifique se há jobs ativos via `GET /tools/routines/scheduled`
