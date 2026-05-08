#!/usr/bin/env bash
# =============================================================================
# bootstrap_tenants.sh — VERSÃO CORRIGIDA
#
# CORREÇÃO CRÍTICA: O endpoint /auth/bootstrap BLOQUEIA depois do 1º usuário!
# Para criar novos tenants use SEMPRE /admin/tenants (requer super admin token).
#
# Uso: bash bootstrap_tenants.sh <API_BASE_URL> <ADMIN_EMAIL> <ADMIN_PASSWORD>
# Exemplo:
#   bash bootstrap_tenants.sh http://187.77.229.227:8000 admin@empresa.com SuaSenha123
# =============================================================================

set -euo pipefail

API="${1:-http://localhost:8000}"
ADMIN_EMAIL="${2:-${ADMIN_EMAIL:-}}"
ADMIN_PASSWORD="${3:-${ADMIN_PASSWORD:-}}"

if [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
  echo "Informe email e senha do super admin:"
  echo "   bash bootstrap_tenants.sh <API_URL> <ADMIN_EMAIL> <ADMIN_PASSWORD>"
  exit 1
fi

echo "========================================"
echo " CRIANDO TENANTS: Mecanica + Fotografia"
echo " API: $API"
echo " Super admin: $ADMIN_EMAIL"
echo "========================================"

echo ""
echo "Fazendo login como super admin..."

LOGIN_RESP=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")

echo "Resposta login: $LOGIN_RESP"

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "Login falhou! Verifique email/senha do super admin."
  exit 1
fi

echo "Token obtido: ${TOKEN:0:30}..."
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo ""
echo "Criando tenant: Auto Center Mecanica..."

RESP_MECANICA=$(curl -s -X POST "$API/admin/tenants" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Auto Center Mecanica",
    "email": "mecanica@empresa.com",
    "plan": "pro",
    "niche": "mecanica",
    "system_prompt": "Voce e o assistente virtual de uma oficina mecanica. Atende clientes de forma prestativa.",
    "bot_display_name": "Assistente Mecanica",
    "welcome_message": "Ola! Sou o assistente do Auto Center. Como posso ajudar?",
    "credits": 3000,
    "user_name": "Admin Mecanica",
    "user_email": "admin@mecanica.com",
    "user_password": "Mecanica@2025"
  }')

echo "Resposta Mecanica: $RESP_MECANICA"
TENANT_ID_MECANICA=$(echo "$RESP_MECANICA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")

echo ""
echo "Criando tenant: Estudio de Fotografia..."

RESP_FOTO=$(curl -s -X POST "$API/admin/tenants" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Estudio de Fotografia",
    "email": "fotografia@empresa.com",
    "plan": "pro",
    "niche": "fotografia",
    "system_prompt": "Voce e o assistente virtual de um estudio de fotografia profissional.",
    "bot_display_name": "Assistente Estudio",
    "welcome_message": "Ola! Seja bem-vindo ao nosso Estudio de Fotografia.",
    "credits": 3000,
    "user_name": "Admin Fotografia",
    "user_email": "admin@fotografia.com",
    "user_password": "Fotografia@2025"
  }')

echo "Resposta Fotografia: $RESP_FOTO"
TENANT_ID_FOTO=$(echo "$RESP_FOTO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")

activate_modules() {
  local TENANT_ID="$1"
  local LABEL="$2"
  if [ -z "$TENANT_ID" ]; then return; fi
  curl -s -X PUT "$API/admin/tenants/$TENANT_ID/modules" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d '{"crm": true, "whatsapp": true, "kanban": true, "agenda": true, "followup": true}'
  echo "Modulos ativados para $LABEL"
}

activate_modules "$TENANT_ID_MECANICA" "Mecanica"
activate_modules "$TENANT_ID_FOTO" "Fotografia"

echo ""
echo "========================================"
echo " CONCLUIDO"
echo "========================================"
echo " MECANICA:   admin@mecanica.com / Mecanica@2025"
echo " FOTOGRAFIA: admin@fotografia.com / Fotografia@2025"
echo "========================================"
