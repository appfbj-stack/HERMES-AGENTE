import asyncio
from datetime import datetime, timezone

import schedule

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models import AssistantMemory, Chat, CrmWhatsAppConnection, Message, Task
from app.services.agent import find_task_refs, mark_task_reminder_sent, task_reminder_already_sent
from app.services.scheduler import start_scheduler
from app.services.telegram import send_telegram_message
from app.services.whatsapp_provider import WhatsAppProviderError, get_provider

_TASK_REMINDER_JOB_TAG = "system_task_reminders"
_task_reminder_started = False
logger = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_scope_from_ref(ref: AssistantMemory) -> tuple[str | None, str | None]:
    parts = ref.key.split(":", 2)
    if len(parts) < 3:
        return None, None
    return None, parts[1]


async def _deliver_task_reminder(db, task: Task, chat: Chat, reminder_text: str) -> bool:
    outbound = Message(
        tenant_id=task.tenant_id,
        chat_id=chat.id,
        sender_type="assistant",
        content=reminder_text,
    )
    db.add(outbound)
    chat.last_message = reminder_text
    chat.last_message_at = _utcnow()
    db.flush()

    if chat.channel == "telegram":
        await send_telegram_message(chat.chat_external_id, reminder_text, tenant_id=task.tenant_id, db=db)
        return True

    if chat.channel == "whatsapp":
        connection = (
            db.query(CrmWhatsAppConnection)
            .filter(CrmWhatsAppConnection.tenant_id == task.tenant_id)
            .first()
        )
        if not connection:
            return True
        try:
            await get_provider(connection).send_text(connection, chat.chat_external_id, reminder_text)
            return True
        except WhatsAppProviderError as exc:
            logger.warning(
                "WhatsApp provider failed to deliver reminder task_id=%s tenant_id=%s chat_id=%s: %s",
                task.id,
                task.tenant_id,
                chat.id,
                exc,
            )
            return False
        except RuntimeError:
            return False

    # Canal web não tem push assíncrono; persistir a mensagem no histórico já é o lembrete disponível.
    return True


def process_due_task_reminders() -> None:
    db = SessionLocal()
    try:
        now = _utcnow()
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
            delivered = False
            for ref in refs:
                _, chat_external_id = _parse_scope_from_ref(ref)
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

                try:
                    delivered = asyncio.run(_deliver_task_reminder(db, task, chat, reminder_text)) or delivered
                except RuntimeError:
                    logger.exception(
                        "Runtime failure delivering task reminder task_id=%s tenant_id=%s chat_id=%s",
                        task.id,
                        task.tenant_id,
                        chat.id,
                    )
                    continue
                except ValueError:
                    logger.exception(
                        "Value failure delivering task reminder task_id=%s tenant_id=%s chat_id=%s",
                        task.id,
                        task.tenant_id,
                        chat.id,
                    )
                    continue

            if delivered:
                mark_task_reminder_sent(db, task.tenant_id, task.id, "delivered")
                db.commit()
    finally:
        db.close()


def start_due_task_reminder_scheduler() -> None:
    global _task_reminder_started
    if _task_reminder_started:
        return

    schedule.every(1).minutes.do(process_due_task_reminders).tag(_TASK_REMINDER_JOB_TAG)
    start_scheduler()
    _task_reminder_started = True
    logger.info("Task reminder scheduler started with 1-minute interval")
