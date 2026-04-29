#!/usr/bin/env python3
"""
Script para testar o login com as credenciais fornecidas.
Execute este script no backend para verificar se há algum problema.
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import verify_password, get_password_hash
from app.models import User, Tenant

def test_login(email: str, password: str, tenant_email: str = None):
    """
    Testa o login com as credenciais fornecidas.
    """
    print(f"=== TESTE DE LOGIN ===\n")
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print(f"Tenant Email: {tenant_email or 'Não fornecido'}\n")

    db = SessionLocal()

    try:
        # Buscar tenant se tenant_email foi fornecido
        if tenant_email:
            print(f"1. Buscando tenant com email: {tenant_email}")
            tenant = db.query(Tenant).filter(
                Tenant.email == tenant_email,
                Tenant.active.is_(True)
            ).first()

            if not tenant:
                print(f"❌ Tenant não encontrado ou inativo")
                return False

            print(f"✅ Tenant encontrado: {tenant.name} (ID: {tenant.id}, Ativo: {tenant.active})")

            # Buscar usuário
            print(f"2. Buscando usuário no tenant")
            user = db.query(User).filter(
                User.tenant_id == tenant.id,
                User.email == email
            ).first()

            if not user:
                print(f"❌ Usuário não encontrado neste tenant")
                return False

            print(f"✅ Usuário encontrado: {user.name} (ID: {user.id}, Role: {user.role})")
        else:
            print(f"1. Buscando usuário por email (sem tenant especificado)")
            users = db.query(User).filter(User.email == email).all()

            if len(users) == 0:
                print(f"❌ Usuário não encontrado")
                return False
            elif len(users) > 1:
                print(f"❌ Múltiplos usuários encontrados com este email")
                print(f"   Por favor, especifique tenant_email")
                for u in users:
                    tenant = db.query(Tenant).filter(Tenant.id == u.tenant_id).first()
                    print(f"   - {tenant.name} ({tenant.email})")
                return False
            else:
                user = users[0]
                print(f"✅ Usuário encontrado: {user.name} (ID: {user.id}, Role: {user.role})")

        # Verificar senha
        print(f"3. Verificando senha")
        if verify_password(password, user.password):
            print(f"✅ Senha correta")
        else:
            print(f"❌ Senha incorreta")
            return False

        # Verificar tenant ativo
        print(f"4. Verificando status do tenant")
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not tenant:
            print(f"❌ Tenant do usuário não encontrado")
            return False

        if not tenant.active:
            print(f"❌ Tenant está inativo")
            return False

        print(f"✅ Tenant está ativo")

        # Informações adicionais
        print(f"\n=== INFORMAÇÕES ADICIONAIS ===")
        print(f"User ID: {user.id}")
        print(f"Tenant ID: {user.tenant_id}")
        print(f"User Name: {user.name}")
        print(f"User Email: {user.email}")
        print(f"User Role: {user.role}")
        print(f"Is Super Admin: {user.is_super_admin}")
        print(f"Tenant Name: {tenant.name}")
        print(f"Tenant Email: {tenant.email}")
        print(f"Tenant Plan: {tenant.plan}")
        print(f"Tenant Active: {tenant.active}")

        print(f"\n=== TESTE DE GERAÇÃO DE TOKEN ===")

        try:
            from app.core.security import create_access_token
            from app.core.config import get_settings

            token = create_access_token(str(user.id), user.tenant_id)
            print(f"✅ Token gerado com sucesso")
            print(f"   Token (primeiros 50 chars): {token[:50]}...")
        except Exception as e:
            print(f"❌ Erro ao gerar token: {e}")
            return False

        print(f"\n✅ LOGIN DEVE FUNCIONAR!")
        return True

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def list_users():
    """
    Lista todos os usuários no sistema.
    """
    print(f"=== LISTA DE USUÁRIOS ===\n")

    db = SessionLocal()

    try:
        users = db.query(User).all()

        print(f"Total de usuários: {len(users)}\n")

        for user in users:
            tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
            print(f"Usuário: {user.name} ({user.email})")
            print(f"  ID: {user.id}")
            print(f"  Role: {user.role}")
            print(f"  Super Admin: {user.is_super_admin}")
            if tenant:
                print(f"  Tenant: {tenant.name} ({tenant.email})")
                print(f"  Tenant Active: {tenant.active}")
            print()

    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Teste de login do Hermes Agente")
    parser.add_argument("--email", help="Email do usuário", required=True)
    parser.add_argument("--password", help="Senha do usuário", required=True)
    parser.add_argument("--tenant-email", help="Email do tenant (opcional)")
    parser.add_argument("--list-users", help="Lista todos os usuários", action="store_true")

    args = parser.parse_args()

    if args.list_users:
        list_users()
    else:
        test_login(args.email, args.password, args.tenant_email)
