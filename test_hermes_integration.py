"""
Script de teste para integração do Hermes Admin
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.config import get_settings
from app.core.database import engine, get_db
from app.models import Base, User
from app.services.hermes_admin import HermesAdminService
from app.services.llm_router import route_llm
from sqlalchemy.orm import Session


def test_database_connection():
    """Testa conexão com banco de dados"""
    try:
        print("🔍 Testando conexão com banco de dados...")
        settings = get_settings()
        
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar banco de dados: {str(e)}")
        return False


def test_llm_router():
    """Testa roteamento LLM"""
    try:
        print("\n🔍 Testando LLM Router...")
        settings = get_settings()
        
        # Verificar se as chaves de API estão configuradas
        if not settings.openrouter_api_key and not settings.deepseek_api_key:
            print("⚠️ Nenhuma API key configurada (OPENROUTER_API_KEY ou DEEPSEEK_API_KEY)")
            return False
        
        print(f"✅ OpenRouter API Key: {'Configurada' if settings.openrouter_api_key else 'Não configurada'}")
        print(f"✅ DeepSeek API Key: {'Configurada' if settings.deepseek_api_key else 'Não configurada'}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar LLM Router: {str(e)}")
        return False


async def test_hermes_admin():
    """Testa Hermes Admin Service"""
    try:
        print("\n🔍 Testando Hermes Admin Service...")
        
        # Criar sessão do banco
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Criar serviço
            service = HermesAdminService(db)
            
            # Verificar se existe usuário super admin
            super_admin = db.query(User).filter(User.is_super_admin).first()
            if not super_admin:
                print("⚠️ Nenhum usuário super_admin encontrado")
                print("💡 Dica: O primeiro usuário será promovido a super_admin automaticamente")
            else:
                print(f"✅ Super admin encontrado: {super_admin.name} ({super_admin.email})")
            
            # Testar dashboard
            dashboard = service.get_dashboard()
            print(f"✅ Dashboard: {dashboard['active_tenants']} tenants ativos")
            
            # Testar criação de tarefa
            from datetime import datetime, timezone, timedelta
            task_data = {
                "title": "Tarefa de teste",
                "description": "Testando Hermes Admin",
                "priority": "normal",
            }
            task = service.create_task(task_data, super_admin if super_admin else User(
                id=0,
                tenant_id=0,
                name="Test",
                email="test@test.com",
                role="admin",
                is_super_admin=True,
                password=""
            ))
            print(f"✅ Tarefa criada: {task.title} (ID: {task.id})")
            
            # Deletar tarefa de teste
            db.delete(task)
            db.commit()
            print("✅ Tarefa de teste deletada")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro ao testar Hermes Admin: {str(e)}")
        return False


def test_telegram_config():
    """Testa configuração do Telegram"""
    try:
        print("\n🔍 Testando configuração do Telegram...")
        settings = get_settings()
        
        print(f"✅ TELEGRAM_BOT_TOKEN: {'Configurado' if settings.telegram_bot_token else 'Não configurado'}")
        print(f"✅ TELEGRAM_ADMIN_TOKEN: {'Configurado' if settings.telegram_admin_token else 'Não configurado'}")
        print(f"✅ HERMES_MASTER_BOT_TOKEN: {'Configurado' if settings.hermes_master_bot_token else 'Não configurado'}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar configuração do Telegram: {str(e)}")
        return False


def test_env_variables():
    """Testa variáveis de ambiente necessárias"""
    try:
        print("\n🔍 Testando variáveis de ambiente...")
        settings = get_settings()
        
        required_vars = {
            "DATABASE_URL": settings.database_url,
            "JWT_SECRET": settings.jwt_secret,
            "OPENROUTER_API_KEY": settings.openrouter_api_key,
            "DEEPSEEK_API_KEY": settings.deepseek_api_key,
        }
        
        missing = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing.append(var_name)
                print(f"❌ {var_name}: Não configurado")
            else:
                print(f"✅ {var_name}: Configurado")
        
        if missing:
            print(f"\n⚠️ Variáveis ausentes: {', '.join(missing)}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar variáveis de ambiente: {str(e)}")
        return False


async def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 Testes de Integração do Hermes Admin")
    print("=" * 60)
    
    results = {
        "Variáveis de Ambiente": test_env_variables(),
        "Conexão Banco de Dados": test_database_connection(),
        "LLM Router": test_llm_router(),
        "Configuração Telegram": test_telegram_config(),
        "Hermes Admin Service": await test_hermes_admin(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Resumo dos Testes")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print("\n" + "=" * 60)
    print(f"Total: {passed_tests}/{total_tests} testes passaram")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("\n🎉 Todos os testes passaram! Sistema pronto para uso.")
        sys.exit(0)
    else:
        print("\n⚠️ Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())