"""
Scheduler de lembretes automáticos de tarefas e AgentReminders.

Correções aplicadas:
  - asyncio.run() era chamado dentro de um loop síncrono (uma chamada por lembrete).
    Agora todas as coroutines pendentes são coletadas e executadas em UMA única
    chamada asyncio.run(asyncio.gather(*coros)), eliminando o risco de
    "This event loop is already running" e múltiplas criações/destruições de loop.
  - Task() transiente era criado apenas para passar tenant_id para _deliver_reminder.
    Agora _deliver_reminder recebe tenant_id diretamente.
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import schedule

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models import AgentReminder, AssistantMemory, Chat, CrmWhatsAppConnection, Message, Task
from app.services.agent import find_task_refs, mark_task_reminder_sent, task_reminder_already_sent
from app.services.scheduler import start_scheduler
from app.services.telegram import send_telegram_message
from app.services.whatsapp_provider import WhatsAppProviderError, get_provider

_TASK_REMINDER_JOB_TAG = "system_task_reminders"
_task_reminder_started = False
logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_scope_from_ref(ref: AssistantMemory) -> str | None:
    """Retorna o chat_external_id embutido na chave taskref:<external_id>:<slug>."""
    parts = ref.key.split(":", 2)
    if len(parts) < 3:
        return None
    return parts[1]


# ---------------------------------------------------------------------------
# Entrega de lembrete (coroutine pura — sem asyncio.run interno)
# ---------------------------------------------------------------------------

async def _deliver_reminder(
    db,
    tenant_id: int,
    chat: Chat,
    reminder_text: str,
) -> bool:
    """
    Persiste a mensagem no histórico e envia via canal correto.
    Retorna True se enviado (ou canal sem push assíncrono).
    Recebe tenant_id diretamente — sem criar objetos ORM transientes.
    """
    outbound = Message(
        tenant_id=tenant_id,
        chat_id=chat.id,
        sender_type="assistant",
        content=reminder_text,
    )
    db.add(outbound)
    chat.last_message = reminder_text
    chat.last_message_at = _utcnow()
    db.flush()

    if chat.channel == "telegram":
        await send_telegram_message(chat.chat_external_id, reminder_text, tenant_id=tenant_id, db=db)
        return True

    if chat.channel == "whatsapp":
        connection = (
            db.query(CrmWhatsAppConnection)
            .filter(CrmWhatsAppConnection.tenant_id == tenant_id)
            .first()
        )
        if not connection:
            return True
        try:
            await get_provider(connection).send_text(connection, chat.chat_external_id, reminder_text)
            return True
        except WhatsAppProviderError as exc:
            logger.warning(
                "WhatsApp provider failed to deliver reminder tenant_id=%s chat_id=%s: %s",
                tenant_id,
                chat.id,
                exc,
            )
            return False
        except RuntimeError:
            return False

    # Canal web: sem push assíncrono — mensagem já está no histórico.
    return True


# ---------------------------------------------------------------------------
# Coleta de jobs pendentes (sync) → execução única via asyncio.run()
# ---------------------------------------------------------------------------

@dataclass
class _PendingDelivery:
    """Dados coletados sincronamente para montar a coroutine depois."""
    coro_factory: Callable  # callable que retorna a coroutine
    on_success: Callable    # callback síncrono chamado após entrega bem-sucedida


def _collect_task_reminders(db, now: datetime) -> list[_PendingDelivery]:
    """Coleta tarefas vencidas e prepara as entregas (sem await)."""
    pending: list[_PendingDelivery] = []

    due_tasks = (
        db.query(Task)
        .filter(
            Task.due_date.is_not(None),
            Task.due_date <= now,
            Task.status.in_(["pending", "open", "pendente"]),
        )
        .order_by(Task.due_date.asc())
        .all()
    )

    for task in due_tasks:
        if task_reminder_already_sent(db, task.tenant_id, task.id):
            continue

        refs = find_task_refs(db, task.tenant_id, task.id)
        for ref in refs:
            chat_external_id = _parse_scope_from_ref(ref)
            if not chat_external_id:
                continue
            chat = (
                db.query(Chat)
                .filter(Chat.tenant_id == task.tenant_id, Chat.chat_external_id == chat_external_id)
                .order_by(Chat.id.desc())
                .first()
            )
            if not chat:
                continue

            reminder_text = f"⏰ Lembrete: {task.title}"
            if task.due_date:
                reminder_text += f" • vencimento {task.due_date.strftime('%d/%m/%Y %H:%M')}"

            # Captura por valor (closure)
            _tenant_id = task.tenant_id
            _task_id = task.id
            _chat = chat
            _text = reminder_text

            def make_task_coro(tid=_tenant_id, ch=_chat, txt=_text):
                return _deliver_reminder(db, tid, ch, txt)

            def on_task_success(tid=_tenant_id, tid2=_task_id):
                mark_task_reminder_sent(db, tid, tid2, "delivered")
                db.commit()

            pending.append(_PendingDelivery(coro_factory=make_task_coro, on_success=on_task_success))

    return pending


def _collect_agent_reminders(db, now: datetime) -> list[_PendingDelivery]:
    """Coleta AgentReminders vencidos e prepara as entregas (sem await)."""
    pending: list[_PendingDelivery] = []

    due_reminders = (
        db.query(AgentReminder)
        .filter(
            AgentReminder.remind_at <= now,
            AgentReminder.status.in_(["pending", "scheduled"]),
        )
        .order_by(AgentReminder.remind_at.asc())
        .all()
    )

    for reminder in due_reminders:
        if reminder.chat_id is None:
            continue
        chat = (
            db.query(Chat)
            .filter(Chat.id == reminder.chat_id, Chat.tenant_id == reminder.tenant_id)
            .first()
        )
        if not chat:
            continue

        reminder_text = f"⏰ Lembrete: {reminder.title}"
        _tenant_id = reminder.tenant_id
        _chat = chat
        _text = reminder_text
        _reminder = reminder

        def make_agent_coro(tid=_tenant_id, ch=_chat, txt=_text):
            return _deliver_reminder(db, tid, ch, txt)

        def on_agent_success(r=_reminder):
            r.status = "sent"
            r.sent_at = now
            db.commit()

        pending.append(_PendingDelivery(coro_factory=make_agent_coro, on_success=on_agent_success))

    return pending


async def _run_all_deliveries(pending: list[_PendingDelivery]) -> list[bool]:
    """Executa todas as entregas em paralelo com asyncio.gather."""
    if not pending:
        return []
    coros = [p.coro_factory() for p in pending]
    return list(await asyncio.gather(*coros, return_exceptions=True))


def process_due_task_reminders() -> None:
    """
    Função principal do scheduler (síncrona).
    Coleta todos os lembretes pendentes, depois executa as entregas
    em UMA única chamada asyncio.run() com gather paralelo.
    """
    db = SessionLocal()
    try:
        now = _utcnow()

        # 1. Coleta síncrona — sem I/O assíncrono
        task_pending = _collect_task_reminders(db, now)
        agent_pending = _collect_agent_reminders(db, now)
        all_pending = task_pending + agent_pending

        if not all_pending:
            return

        # 2. UMA única chamada asyncio.run() para todas as entregas
        results = asyncio.run(_run_all_deliveries(all_pending))

        # 3. Processa resultados e dispara callbacks de sucesso
        for delivery, result in zip(all_pending, results):
            if isinstance(result, Exception):
                logger.exception(
                    "Falha ao entregar lembrete: %s", result,
                    exc_info=result,
                )
                continue
            if result:
                try:
                    delivery.on_success()
                except Exception:
                    logger.exception("Falha no callback on_success de lembrete")

    except Exception:
        logger.exception("Erro inesperado no process_due_task_reminders")
    finally:
        db.close()


def start_due_task_reminder_scheduler() -> None:
    global _task_reminder_started
    if _task_reminder_started:
        return

    schedule.every(1).minutes.do(process_due_task_reminders).tag(_TASK_REMINDER_JOB_TAG)
    start_scheduler()
    _task_reminder_started = True
    logger.info("Task reminder scheduler iniciado — intervalo de 1 minuto")
