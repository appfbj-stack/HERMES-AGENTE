import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.models import AgentAppointment, AgentReminder, AssistantMemory, ClientMemory, ClientSkill, CrmWhatsAppConnection, Message, Task, TenantModule
from app import main as app_main
from app.routes import public as public_routes
from app.routes import health as health_routes
from app.routes import webhook as webhook_routes
from app.routes import admin_hermes as admin_hermes_routes
from app.routes.admin import list_tenants, set_tenant_modules
from app.routes.auth import login, logout
from app.routes.client import activate_client_skill_route, create_client_skill, get_client_profile, list_client_skills, list_client_suggestions, toggle_client_skill, update_client_profile
from app.routes.messages import send_message
from app.routes.public import PublicSendRequest
from app.schemas import ClientProfileUpdate, ClientSkillActivationRequest, ClientSkillCreate, ClientSkillToggleRequest, LoginRequest, TenantModuleUpdate
from app.services import task_reminders
from app.services.agent import (
    maybe_handle_memory_query,
    maybe_handle_task_query,
    process_inbound_automation,
    task_reminder_already_sent,
)
from app.services.modules import build_modules_out
from app.services.telegram import send_telegram_message

from conftest import TestingSessionLocal, create_chat, create_tenant, create_user


class _FakeConnection:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.executed: list[str] = []
        self.rollbacks = 0
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        sql = str(statement)
        self.executed.append(sql)
        if self.should_fail and "FAIL SQL" in sql:
            raise RuntimeError("boom")
        return 1

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _FakeEngine:
    def __init__(self, connection: _FakeConnection):
        self.connection = connection

    def connect(self):
        return self.connection


def test_login_requires_tenant_email_when_same_email_exists_in_multiple_tenants(db_session):
    tenant_a = create_tenant(db_session, name="Tenant A", email="a@empresa.com")
    tenant_b = create_tenant(db_session, name="Tenant B", email="b@empresa.com")
    create_user(db_session, tenant_id=tenant_a.id, name="Ana", email="duplicado@empresa.com")
    create_user(db_session, tenant_id=tenant_b.id, name="Bia", email="duplicado@empresa.com")
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        login(
            LoginRequest(email="duplicado@empresa.com", password="Senha123!"),
            db=db_session,
        )

    assert exc_info.value.status_code == 400
    assert "mais de uma empresa" in exc_info.value.detail


def test_run_startup_migrations_raises_on_first_failure(monkeypatch):
    connection = _FakeConnection(should_fail=True)

    monkeypatch.setattr(app_main, "engine", _FakeEngine(connection))
    monkeypatch.setattr(app_main, "MIGRATIONS", ["SELECT 1", "FAIL SQL", "SELECT 2"])

    with pytest.raises(RuntimeError) as exc_info:
        app_main.run_startup_migrations()

    assert "Startup migrations failed" in str(exc_info.value)
    assert connection.commits == 2
    assert connection.rollbacks == 1


def test_health_reports_database_check(monkeypatch):
    connection = _FakeConnection()

    monkeypatch.setattr(health_routes, "engine", _FakeEngine(connection))

    payload = health_routes.health()

    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert connection.executed


def test_resolve_tenant_id_ignores_inactive_tenant_fallbacks(db_session):
    inactive_tenant = create_tenant(db_session, name="Inactive", email="inactive@empresa.com", active=False)
    inactive_tenant.telegram_bot_token = "tenant-token-inactive"
    db_session.commit()

    by_query = webhook_routes._resolve_tenant_id(
        db_session,
        chat_external_id="telegram-user-1",
        inbound_text="oi",
        bot_token_received=None,
        fallback_query=inactive_tenant.id,
    )
    by_token = webhook_routes._resolve_tenant_id(
        db_session,
        chat_external_id="telegram-user-1",
        inbound_text="oi",
        bot_token_received="tenant-token-inactive",
        fallback_query=None,
    )

    assert by_query is None
    assert by_token is None


def test_generic_telegram_webhook_rejects_admin_tokens(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.services.telegram.get_settings",
        lambda: type(
            "StubSettings",
            (),
            {
                "telegram_admin_token": "admin-token",
                "hermes_master_bot_token": "master-token",
            },
        )(),
    )
    monkeypatch.setattr(
        webhook_routes,
        "get_settings",
        lambda: type(
            "StubSettings",
            (),
            {
                "max_input_chars": 800,
                "hermes_master_bot_token": "master-token",
            },
        )(),
    )

    payload = {
        "message": {
            "text": "oi",
            "chat": {"id": 123},
            "from": {"id": 123, "first_name": "Admin"},
        }
    }

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            webhook_routes.telegram_webhook(
                payload=payload,
                bot_token="admin-token",
                x_telegram_bot_api_secret_token=None,
                db=db_session,
            )
        )

    assert exc_info.value.status_code == 401


def test_login_request_accepts_blank_tenant_email_as_none():
    payload = LoginRequest(email="user@empresa.com", password="Senha123!", tenant_email="")

    assert payload.tenant_email is None


def test_set_tenant_modules_updates_flags_for_tenant(db_session):
    admin_tenant = create_tenant(db_session, name="Admin", email="admin@empresa.com")
    admin_user = create_user(
        db_session,
        tenant_id=admin_tenant.id,
        name="Super",
        email="super@empresa.com",
        is_super_admin=True,
    )
    target_tenant = create_tenant(db_session, name="Cliente", email="cliente@empresa.com")
    db_session.commit()

    response = set_tenant_modules(
        target_tenant.id,
        TenantModuleUpdate(crm=True, whatsapp=True, kanban=True, content_publisher=True),
        _=admin_user,
        db=db_session,
    )

    modules = db_session.query(TenantModule).filter(TenantModule.tenant_id == target_tenant.id).first()
    assert modules is not None
    assert modules.crm is True
    assert modules.whatsapp is True
    assert modules.kanban is True
    assert modules.content_publisher is True
    assert response["crm_enabled"] is True
    assert response["content_publisher_enabled"] is True


def test_list_tenants_returns_admin_module_flags_for_super_admin(db_session):
    admin_tenant = create_tenant(db_session, name="Admin", email="admin-master@empresa.com")
    admin_user = create_user(
        db_session,
        tenant_id=admin_tenant.id,
        name="Super",
        email="super-master@empresa.com",
        is_super_admin=True,
    )
    target_tenant = create_tenant(
        db_session,
        name="Cliente CRM",
        email="cliente-crm@empresa.com",
        modules={"crm": True, "whatsapp": True, "kanban": True},
    )
    db_session.commit()

    response = list_tenants(_=admin_user, db=db_session)
    target_payload = next(item for item in response if item["id"] == target_tenant.id)

    assert target_payload["crm_enabled"] is True
    assert target_payload["whatsapp_enabled"] is True
    assert target_payload["whatsapp_evolution_enabled"] is True
    assert target_payload["kanban_enabled"] is True


def test_tenant_modules_support_explicit_whatsapp_evolution_and_followup_flags(db_session):
    tenant = create_tenant(
        db_session,
        name="Cliente Modulos",
        email="modulos@empresa.com",
        modules={"whatsapp_evolution": True, "followup": True},
    )
    db_session.commit()

    modules = db_session.query(TenantModule).filter(TenantModule.tenant_id == tenant.id).first()
    assert modules is not None
    payload = build_modules_out(modules)

    assert payload.whatsapp_evolution is True
    assert payload.whatsapp is True
    assert payload.followup is True


def test_hermes_admin_chat_accepts_authenticated_super_admin(db_session, monkeypatch):
    admin_tenant = create_tenant(db_session, name="Admin", email="admin-hermes@empresa.com")
    admin_user = create_user(
        db_session,
        tenant_id=admin_tenant.id,
        name="Super",
        email="super-hermes@empresa.com",
        is_super_admin=True,
    )
    db_session.commit()

    class FakeHermesAdminService:
        def __init__(self, db):
            self.db = db

        async def chat(self, user, message):
            return {"response": f"echo:{message}"}

    monkeypatch.setattr(admin_hermes_routes, "HermesAdminService", FakeHermesAdminService)

    response = asyncio.run(
        admin_hermes_routes.hermes_chat(
            payload=type("Payload", (), {"message": "oi"})(),
            db=db_session,
            user=admin_user,
        )
    )

    assert response["response"] == "echo:oi"


def test_logout_returns_success_for_authenticated_user(db_session):
    tenant = create_tenant(db_session, name="Tenant Auth", email="auth@empresa.com")
    user = create_user(db_session, tenant_id=tenant.id, name="Auth User", email="auth-user@empresa.com")
    db_session.commit()

    response = logout(current_user=user)

    assert response["success"] is True
    assert "Logout realizado" in response["message"]


def test_settings_accept_legacy_auth_env_names():
    settings = Settings.model_validate(
        {
            "DATABASE_URL": "sqlite://",
            "SECRET_KEY": "legacy-secret-key-with-at-least-32-chars",
            "JWT_EXPIRE_MINUTES": 30,
            "ADMIN_EMAIL": "admin@empresa.com",
            "ADMIN_PASSWORD": "Senha123!",
        }
    )

    assert settings.jwt_secret == "legacy-secret-key-with-at-least-32-chars"
    assert settings.access_token_expire_minutes == 30
    assert settings.admin_email == "admin@empresa.com"
    assert settings.admin_password == "Senha123!"


def test_env_super_admin_seed_updates_existing_user_password_and_role(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Admin Tenant", email="borgesjaf@gmail.com", active=False)
    create_user(
        db_session,
        tenant_id=tenant.id,
        name="Fernando",
        email="borgesjaf@gmail.com",
        password="SenhaAntiga123!",
        role="agent",
        is_super_admin=False,
    )
    db_session.commit()

    monkeypatch.setattr(app_main, "engine", TestingSessionLocal.kw["bind"])
    monkeypatch.setattr(
        app_main,
        "settings",
        type(
            "StubSettings",
            (),
            {"admin_email": "borgesjaf@gmail.com", "admin_password": "HermesAdmin@2026#Segura"},
        )(),
    )

    app_main.ensure_env_super_admin()

    refreshed_user = db_session.query(app_main.User).filter(app_main.User.email == "borgesjaf@gmail.com").first()
    refreshed_tenant = db_session.query(app_main.Tenant).filter(app_main.Tenant.id == tenant.id).first()

    assert refreshed_user is not None
    assert refreshed_user.is_super_admin is True
    assert refreshed_user.role == "admin"
    assert refreshed_tenant is not None and refreshed_tenant.active is True
    login(LoginRequest(email="borgesjaf@gmail.com", password="HermesAdmin@2026#Segura"), db=db_session)


def test_login_env_super_admin_fallback_rehashes_mismatched_password(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Admin Tenant", email="admin-tenant@empresa.com", active=True)
    create_user(
        db_session,
        tenant_id=tenant.id,
        name="Fernando",
        email="fernandojaborges@gmail.com",
        password="OutraSenha123!",
        role="admin",
        is_super_admin=True,
    )
    db_session.commit()

    monkeypatch.setattr(
        "app.routes.auth.get_settings",
        lambda: type(
            "StubSettings",
            (),
            {"admin_email": "fernandojaborges@gmail.com", "admin_password": "HermesAdmin@2026#Segura"},
        )(),
    )

    response = login(LoginRequest(email="fernandojaborges@gmail.com", password="HermesAdmin@2026#Segura"), db=db_session)
    refreshed_user = db_session.query(app_main.User).filter(app_main.User.email == "fernandojaborges@gmail.com").first()

    assert response.access_token
    assert refreshed_user is not None
    assert login(LoginRequest(email="fernandojaborges@gmail.com", password="HermesAdmin@2026#Segura"), db=db_session)


def test_login_auto_syncs_env_super_admin_when_user_is_missing(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.get_settings",
        lambda: type(
            "StubSettings",
            (),
            {
                "admin_email": "borgesjaf@gmail.com",
                "admin_password": "HermesAdmin@2026#Segura",
            },
        )(),
    )
    def fake_ensure_env_super_admin():
        tenant = create_tenant(db_session, name="Admin Master", email="borgesjaf@gmail.com", active=True)
        create_user(
            db_session,
            tenant_id=tenant.id,
            name="Admin Master",
            email="borgesjaf@gmail.com",
            password="HermesAdmin@2026#Segura",
            role="admin",
            is_super_admin=True,
        )
        db_session.commit()

    monkeypatch.setattr("app.main.ensure_env_super_admin", fake_ensure_env_super_admin)

    response = login(LoginRequest(email="borgesjaf@gmail.com", password="HermesAdmin@2026#Segura"), db=db_session)
    seeded_user = db_session.query(app_main.User).filter(app_main.User.email == "borgesjaf@gmail.com").first()
    seeded_tenant = db_session.query(app_main.Tenant).filter(app_main.Tenant.email == "borgesjaf@gmail.com").first()

    assert response.access_token
    assert seeded_user is not None
    assert seeded_user.is_super_admin is True
    assert seeded_user.role == "admin"
    assert seeded_tenant is not None
    assert seeded_tenant.active is True


def test_login_matches_email_case_insensitively(db_session):
    tenant = create_tenant(db_session, name="Tenant Case", email="empresa@teste.com")
    create_user(
        db_session,
        tenant_id=tenant.id,
        name="Fernando",
        email="borgesjaf@gmail.com",
        password="HermesAdmin@2026#Segura",
    )
    db_session.commit()

    response = login(
        LoginRequest(
            email="BORGESJAF@GMAIL.COM",
            password="HermesAdmin@2026#Segura",
            tenant_email="EMPRESA@TESTE.COM",
        ),
        db=db_session,
    )

    assert response.access_token


def test_login_allows_env_super_admin_even_with_wrong_tenant_email(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.get_settings",
        lambda: type(
            "StubSettings",
            (),
            {
                "admin_email": "borgesjaf@gmail.com",
                "admin_password": "HermesAdmin@2026#Segura",
            },
        )(),
    )

    def fake_ensure_env_super_admin():
        tenant = create_tenant(db_session, name="Admin Master", email="admin-master@empresa.com", active=True)
        create_user(
            db_session,
            tenant_id=tenant.id,
            name="Admin Master",
            email="borgesjaf@gmail.com",
            password="HermesAdmin@2026#Segura",
            role="admin",
            is_super_admin=True,
        )
        db_session.commit()

    monkeypatch.setattr("app.main.ensure_env_super_admin", fake_ensure_env_super_admin)

    response = login(
        LoginRequest(
            email="borgesjaf@gmail.com",
            password="HermesAdmin@2026#Segura",
            tenant_email="tenant-errado@empresa.com",
        ),
        db=db_session,
    )

    assert response.access_token


def test_login_normalizes_wrapped_env_admin_credentials(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.get_settings",
        lambda: type(
            "StubSettings",
            (),
            {
                "admin_email": '  "borgesjaf@gmail.com"  ',
                "admin_password": "  'HermesAdmin@2026#Segura'  ",
            },
        )(),
    )

    def fake_ensure_env_super_admin():
        tenant = create_tenant(db_session, name="Admin Master", email="admin-master@empresa.com", active=True)
        create_user(
            db_session,
            tenant_id=tenant.id,
            name="Admin Master",
            email="borgesjaf@gmail.com",
            password="HermesAdmin@2026#Segura",
            role="admin",
            is_super_admin=True,
        )
        db_session.commit()

    monkeypatch.setattr("app.main.ensure_env_super_admin", fake_ensure_env_super_admin)

    response = login(
        LoginRequest(
            email="borgesjaf@gmail.com",
            password="HermesAdmin@2026#Segura",
        ),
        db=db_session,
    )

    assert response.access_token


def test_hermes_automation_persists_memory_and_tasks_scoped_to_chat(db_session):
    tenant = create_tenant(db_session, name="Tenant", email="tenant@empresa.com")
    chat_a = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-a")
    chat_b = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-b")

    confirmations_memory = process_inbound_automation(
        db_session,
        tenant.id,
        chat_a,
        "guarde que o seminário de missões é dia 16/05",
    )
    confirmations_reminder = process_inbound_automation(
        db_session,
        tenant.id,
        chat_a,
        "me lembre de ajustar o CRM amanhã às 8",
    )
    db_session.commit()

    memory_reply = maybe_handle_memory_query(db_session, tenant.id, chat_a, "o que você guardou?")
    other_chat_memory_reply = maybe_handle_memory_query(db_session, tenant.id, chat_b, "o que você guardou?")
    task_reply = maybe_handle_task_query(db_session, tenant.id, chat_a, "quais tarefas")
    other_chat_task_reply = maybe_handle_task_query(db_session, tenant.id, chat_b, "quais tarefas")

    reminder = db_session.query(AgentReminder).filter(AgentReminder.tenant_id == tenant.id).first()

    assert any("Salvo na memória" in item for item in confirmations_memory)
    assert any("Lembrete criado" in item for item in confirmations_reminder)
    assert memory_reply is not None and "seminário de missões" in memory_reply
    assert other_chat_memory_reply == "Ainda não encontrei memórias salvas para esta conversa."
    assert task_reply is not None and "ajustar o CRM" in task_reply
    assert other_chat_task_reply == "Ainda não encontrei tarefas ou lembretes salvos para esta conversa."
    assert reminder is not None and reminder.remind_at is not None


def test_hermes_automation_creates_task_and_appointment_formally(db_session):
    tenant = create_tenant(db_session, name="Tenant Ops", email="ops@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-ops")

    confirmations_task = process_inbound_automation(
        db_session,
        tenant.id,
        chat,
        "preciso ajustar o CRM hoje às 18:00",
    )
    confirmations_appointment = process_inbound_automation(
        db_session,
        tenant.id,
        chat,
        "agendar reunião com o cliente amanhã às 10:00",
    )
    db_session.commit()

    task = db_session.query(Task).filter(Task.tenant_id == tenant.id).first()
    appointment = db_session.query(AgentAppointment).filter(AgentAppointment.tenant_id == tenant.id).first()
    task_reply = maybe_handle_task_query(db_session, tenant.id, chat, "o que está agendado")

    assert any("Tarefa criada" in item for item in confirmations_task)
    assert any("Agendamento registrado" in item for item in confirmations_appointment)
    assert task is not None and task.due_date is not None
    assert appointment is not None and appointment.scheduled_at is not None
    assert task_reply is not None and "agendamento:" in task_reply


def test_client_memory_is_isolated_per_tenant(db_session):
    tenant_a = create_tenant(db_session, name="Tenant A", email="ta@empresa.com")
    tenant_b = create_tenant(db_session, name="Tenant B", email="tb@empresa.com")
    chat_a = create_chat(db_session, tenant_id=tenant_a.id, external_id="sessao-a")
    chat_b = create_chat(db_session, tenant_id=tenant_b.id, external_id="sessao-b")

    process_inbound_automation(db_session, tenant_a.id, chat_a, "preciso fazer follow-up com os leads")
    process_inbound_automation(db_session, tenant_a.id, chat_a, "vou agendar reunião com os clientes")
    process_inbound_automation(db_session, tenant_b.id, chat_b, "respondo à noite")
    db_session.commit()

    tenant_a_memory = db_session.query(ClientMemory).filter(ClientMemory.tenant_id == tenant_a.id).all()
    tenant_b_memory = db_session.query(ClientMemory).filter(ClientMemory.tenant_id == tenant_b.id).all()

    assert any(item.chave == "followup_mentions" for item in tenant_a_memory)
    assert all(item.chave != "horario_resposta" for item in tenant_a_memory)
    assert any(item.chave == "horario_resposta" for item in tenant_b_memory)
    assert all(item.tenant_id == tenant_a.id for item in tenant_a_memory)
    assert all(item.tenant_id == tenant_b.id for item in tenant_b_memory)


def test_hermes_learns_patterns_and_suggests_without_auto_activating_skills(db_session):
    tenant = create_tenant(db_session, name="Tenant Learn", email="learn@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-learn")

    confirmations_1 = process_inbound_automation(db_session, tenant.id, chat, "preciso fazer follow-up do lead 1")
    confirmations_2 = process_inbound_automation(db_session, tenant.id, chat, "vamos fazer follow-up do lead 2")
    confirmations_3 = process_inbound_automation(db_session, tenant.id, chat, "mais um follow-up para amanhã")
    db_session.commit()

    followup_counter = (
        db_session.query(ClientMemory)
        .filter(
            ClientMemory.tenant_id == tenant.id,
            ClientMemory.tipo == "comportamento",
            ClientMemory.chave == "followup_mentions",
        )
        .first()
    )
    suggestion_marker = (
        db_session.query(ClientMemory)
        .filter(
            ClientMemory.tenant_id == tenant.id,
            ClientMemory.tipo == "insight",
            ClientMemory.chave == "suggestion:follow_up_automatico",
        )
        .first()
    )
    skills = db_session.query(ClientSkill).filter(ClientSkill.tenant_id == tenant.id).all()

    assert all("follow-up automático" not in item for item in confirmations_1)
    assert all("follow-up automático" not in item for item in confirmations_2)
    assert any("follow-up automático" in item for item in confirmations_3)
    assert followup_counter is not None and "\"count\":3" in followup_counter.valor
    assert suggestion_marker is not None
    assert skills == []


def test_explicit_skill_activation_creates_active_client_skill(db_session):
    tenant = create_tenant(db_session, name="Tenant Skill", email="skill@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-skill")

    process_inbound_automation(db_session, tenant.id, chat, "preciso fazer follow-up do lead 1")
    process_inbound_automation(db_session, tenant.id, chat, "preciso fazer follow-up do lead 2")
    process_inbound_automation(db_session, tenant.id, chat, "preciso fazer follow-up do lead 3")
    confirmations = process_inbound_automation(db_session, tenant.id, chat, "pode ativar o follow-up automático")
    db_session.commit()

    skill = (
        db_session.query(ClientSkill)
        .filter(ClientSkill.tenant_id == tenant.id, ClientSkill.nome_skill == "follow_up_automatico")
        .first()
    )

    assert any("Skill ativada com sua confirmação" in item for item in confirmations)
    assert skill is not None
    assert skill.ativa is True


def test_client_profile_and_skill_routes_are_scoped_to_current_tenant(db_session):
    tenant_a = create_tenant(db_session, name="Tenant A", email="route-a@empresa.com")
    tenant_b = create_tenant(db_session, name="Tenant B", email="route-b@empresa.com")
    user_a = create_user(db_session, tenant_id=tenant_a.id, name="User A", email="user-a@empresa.com")
    user_b = create_user(db_session, tenant_id=tenant_b.id, name="User B", email="user-b@empresa.com")
    db_session.commit()

    updated_profile = update_client_profile(
        ClientProfileUpdate(tipo_negocio="Clínica", objetivo="Responder mais rápido", nivel_automacao="medio"),
        db=db_session,
        current_user=user_a,
    )
    created_skill = create_client_skill(
        ClientSkillCreate(nome_skill="campanha_simples", descricao="Skill manual", ativa=False, configuracao="{\"channel\":\"crm\"}"),
        db=db_session,
        current_user=user_a,
    )
    toggled_skill = toggle_client_skill(
        created_skill.id,
        ClientSkillToggleRequest(ativa=True),
        db=db_session,
        current_user=user_a,
    )

    profile_a = get_client_profile(db=db_session, current_user=user_a)
    profile_b = get_client_profile(db=db_session, current_user=user_b)
    skills_a = list_client_skills(db=db_session, current_user=user_a)
    skills_b = list_client_skills(db=db_session, current_user=user_b)
    suggestions_a = list_client_suggestions(db=db_session, current_user=user_a)
    suggestions_b = list_client_suggestions(db=db_session, current_user=user_b)

    assert updated_profile.tenant_id == tenant_a.id
    assert updated_profile.tipo_negocio == "Clínica"
    assert toggled_skill.ativa is True
    assert profile_a.tenant_id == tenant_a.id
    assert profile_b.tenant_id == tenant_b.id
    assert len(skills_a) == 1
    assert skills_a[0].tenant_id == tenant_a.id
    assert skills_b == []
    assert suggestions_a == []
    assert suggestions_b == []


def test_client_suggestion_activation_route_creates_skill_in_current_tenant_only(db_session):
    tenant_a = create_tenant(db_session, name="Tenant A", email="activate-a@empresa.com")
    tenant_b = create_tenant(db_session, name="Tenant B", email="activate-b@empresa.com")
    user_a = create_user(db_session, tenant_id=tenant_a.id, name="User A", email="activate-user-a@empresa.com")
    user_b = create_user(db_session, tenant_id=tenant_b.id, name="User B", email="activate-user-b@empresa.com")
    chat_a = create_chat(db_session, tenant_id=tenant_a.id, external_id="activate-chat-a")
    create_chat(db_session, tenant_id=tenant_b.id, external_id="activate-chat-b")

    process_inbound_automation(db_session, tenant_a.id, chat_a, "preciso de follow-up")
    process_inbound_automation(db_session, tenant_a.id, chat_a, "mais follow-up")
    process_inbound_automation(db_session, tenant_a.id, chat_a, "outro follow-up")
    db_session.commit()

    activated = activate_client_skill_route(
        ClientSkillActivationRequest(skill_key="follow_up_automatico"),
        db=db_session,
        current_user=user_a,
    )
    skills_a = list_client_skills(db=db_session, current_user=user_a)
    skills_b = list_client_skills(db=db_session, current_user=user_b)

    assert activated.tenant_id == tenant_a.id
    assert activated.ativa is True
    assert len(skills_a) == 1
    assert skills_a[0].nome_skill == "follow_up_automatico"
    assert skills_b == []


def test_public_chat_send_returns_hermes_reply_and_persists_messages(db_session, monkeypatch):
    tenant = create_tenant(
        db_session,
        name="Tenant Web",
        email="web@empresa.com",
        modules={"crm": False},
        credits=10,
    )
    db_session.commit()

    async def fake_generate_reply(messages, tenant_id=None):
        return "Resposta Hermes", 7

    monkeypatch.setattr(public_routes, "generate_reply", fake_generate_reply)

    response = asyncio.run(
        public_routes.public_chat_send(
            tenant.id,
            PublicSendRequest(session_id="sessao-web-123", visitor_name="Fernando", content="oi"),
            db=db_session,
        )
    )

    messages = db_session.query(Message).order_by(Message.id.asc()).all()

    assert response.blocked is False
    assert response.assistant_message is not None
    assert response.assistant_message.content == "Resposta Hermes"
    assert len(messages) == 2
    assert messages[0].sender_type == "user"
    assert messages[1].sender_type == "assistant"


def test_due_task_reminder_creates_message_and_marks_task_as_notified(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Tenant Reminder", email="reminder@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-reminder", channel="web")
    task = Task(
        tenant_id=tenant.id,
        title="Revisar CRM",
        due_date=datetime.now(timezone.utc) - timedelta(minutes=2),
        status="pending",
    )
    db_session.add(task)
    db_session.flush()
    db_session.add(
        AssistantMemory(
            tenant_id=tenant.id,
            key=f"taskref:{chat.chat_external_id}:revisar-crm",
            value=str(task.id),
        )
    )
    db_session.commit()

    monkeypatch.setattr(task_reminders, "SessionLocal", TestingSessionLocal)
    task_reminders.process_due_task_reminders()

    refreshed_session = TestingSessionLocal()
    try:
        reminder_message = (
            refreshed_session.query(Message)
            .filter(Message.chat_id == chat.id, Message.sender_type == "assistant")
            .order_by(Message.id.desc())
            .first()
        )
        assert reminder_message is not None
        assert "⏰ Lembrete: Revisar CRM" in reminder_message.content
        assert task_reminder_already_sent(refreshed_session, tenant.id, task.id) is True
    finally:
        refreshed_session.close()


def test_due_agent_reminder_creates_message_and_marks_reminder_as_sent(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Tenant Agent Reminder", email="agent-reminder@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="sessao-agent-reminder", channel="web")
    reminder = AgentReminder(
        tenant_id=tenant.id,
        chat_id=chat.id,
        title="Enviar proposta",
        remind_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status="pending",
    )
    db_session.add(reminder)
    db_session.commit()

    monkeypatch.setattr(task_reminders, "SessionLocal", TestingSessionLocal)
    task_reminders.process_due_task_reminders()

    refreshed_session = TestingSessionLocal()
    try:
        reminder_message = (
            refreshed_session.query(Message)
            .filter(Message.chat_id == chat.id, Message.sender_type == "assistant")
            .order_by(Message.id.desc())
            .first()
        )
        refreshed_reminder = refreshed_session.query(AgentReminder).filter(AgentReminder.id == reminder.id).first()
        assert reminder_message is not None
        assert "⏰ Lembrete: Enviar proposta" in reminder_message.content
        assert refreshed_reminder is not None
        assert refreshed_reminder.status == "sent"
        assert refreshed_reminder.sent_at is not None
    finally:
        refreshed_session.close()


def test_send_message_uses_telegram_channel_only_for_telegram_chat(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Tenant Telegram", email="telegram@empresa.com", credits=10)
    user = create_user(db_session, tenant_id=tenant.id, name="Admin", email="telegram-user@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="telegram-chat", channel="telegram")
    db_session.commit()

    calls: list[tuple[str, str]] = []

    async def fake_send(chat_external_id: str, text: str, **kwargs):
        calls.append((chat_external_id, text))

    monkeypatch.setattr("app.routes.messages.send_telegram_message", fake_send)

    response = asyncio.run(
        send_message(
            chat.id,
            payload=type("Payload", (), {"content": "Olá Telegram"})(),
            db=db_session,
            current_user=user,
            credit=db_session.query(app_main.Credit).filter(app_main.Credit.tenant_id == tenant.id).first(),
        )
    )

    assert response.content == "Olá Telegram"
    assert calls == [("telegram-chat", "Olá Telegram")]


def test_send_message_uses_whatsapp_provider_for_whatsapp_chat(db_session, monkeypatch):
    tenant = create_tenant(db_session, name="Tenant WhatsApp", email="whatsapp@empresa.com", credits=10)
    user = create_user(db_session, tenant_id=tenant.id, name="Admin", email="whatsapp-user@empresa.com")
    chat = create_chat(db_session, tenant_id=tenant.id, external_id="5511999999999", channel="whatsapp")
    db_session.add(
        CrmWhatsAppConnection(
            tenant_id=tenant.id,
            provider="evolution_go",
            instance_name="tenant-whatsapp",
            api_base_url="https://evolution.example.com",
            api_key="secret",
            status="connected",
        )
    )
    db_session.commit()

    sent_payloads: list[tuple[str, str]] = []

    class FakeProvider:
        async def send_text(self, connection, number: str, text: str):
            sent_payloads.append((number, text))
            return {"success": True}

    monkeypatch.setattr("app.routes.messages.get_provider", lambda connection: FakeProvider())

    response = asyncio.run(
        send_message(
            chat.id,
            payload=type("Payload", (), {"content": "Olá WhatsApp"})(),
            db=db_session,
            current_user=user,
            credit=db_session.query(app_main.Credit).filter(app_main.Credit.tenant_id == tenant.id).first(),
        )
    )

    assert response.content == "Olá WhatsApp"
    assert sent_payloads == [("5511999999999", "Olá WhatsApp")]
