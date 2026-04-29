#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.core.config import get_settings

    s = get_settings()

    print("=== VERIFICAÇÃO DE CONFIGURAÇÕES ===\n")

    # JWT_SECRET
    jwt_secret = "✅ DEFINIDO" if s.jwt_secret else "❌ NÃO DEFINIDO"
    print(f"JWT_SECRET: {jwt_secret}")
    if s.jwt_secret:
        print(f"  Tamanho: {len(s.jwt_secret)} caracteres")

    # CORS_ORIGINS
    print(f"\nCORS_ORIGINS: {len(s.cors_origins)} origens")
    for i, origin in enumerate(s.cors_origins, 1):
        print(f"  {i}. {origin}")

    # ACCESS_TOKEN_EXPIRE_MINUTES
    print(f"\nACCESS_TOKEN_EXPIRE_MINUTES: {s.access_token_expire_minutes}")

    # DATABASE_URL
    db_url = s.database_url
    if db_url:
        print(f"\nDATABASE_URL: ✅ DEFINIDO")
        print(f"  Database: {db_url.split('@')[-1].split('/')[0]}")
    else:
        print(f"\nDATABASE_URL: ❌ NÃO DEFINIDO")

    print("\n=== STATUS ===")
    all_ok = s.jwt_secret and s.cors_origins and s.database_url
    if all_ok:
        print("✅ Todas as configurações críticas estão definidas")
    else:
        print("❌ Algumas configurações críticas estão faltando!")

except Exception as e:
    print(f"❌ Erro ao verificar configurações: {e}")
    print("❌ Certifique-se de que as variáveis de ambiente estão definidas")
