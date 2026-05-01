import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.models import AssistantMemory, Message, Task, TenantModule
from app.routes import public as public_routes
from app.routes.admin import set_tenant_modules
from app.routes.auth import login, logout
from app.routes.public import PublicSendRequest
from app.schemas import LoginRequest, TenantModuleUpdate
from app.services import task_reminders
from app.services.agent import (
    maybe_handle_memory_query,
    maybe_handle_task_query,
    process_inbound_automation,
    task_reminder_already_sent,
)

from conftest import TestingSessionLocal, create_chat, create_tenant, create_user


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
    confirmations_task = process_inbound_automation(
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

    task = db_session.query(Task).filter(Task.tenant_id == tenant.id).first()

    assert any("Salvo na memória" in item for item in confirmations_memory)
    assert any("Tarefa criada" in item for item in confirmations_task)
    assert memory_reply is not None and "seminário de missões" in memory_reply
    assert other_chat_memory_reply == "Ainda não encontrei memórias salvas para esta conversa."
    assert task_reply is not None and "ajustar o CRM" in task_reply
    assert other_chat_task_reply == "Ainda não encontrei tarefas ou lembretes salvos para esta conversa."
    assert task is not None and task.due_date is not None


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
