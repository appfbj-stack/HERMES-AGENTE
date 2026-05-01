from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AgentAppointment, AgentReminder, AssistantMemory, Chat, Task


def _memory_key_prefix(chat: Chat) -> str:
    return f"chat:{chat.chat_external_id}:"


def _task_ref_key_prefix(chat: Chat) -> str:
    return f"taskref:{chat.chat_external_id}:"


def _slugify_key(text: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in text.strip())
    collapsed = "-".join(part for part in safe.split("-") if part)
    return collapsed[:48] or "registro"


def save_memory(db: Session, tenant_id: int, chat: Chat, content: str) -> AssistantMemory:
    memory_key = f"{_memory_key_prefix(chat)}{_slugify_key(content)}"
    memory = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id, AssistantMemory.key == memory_key)
        .first()
    )
    if not memory:
        memory = AssistantMemory(tenant_id=tenant_id, key=memory_key, value=content[:4000])
        db.add(memory)
    else:
        memory.value = content[:4000]
    return memory


def search_memory(db: Session, tenant_id: int, chat: Chat, term: str | None = None) -> list[AssistantMemory]:
    query = (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.key.like(f"{_memory_key_prefix(chat)}%"),
        )
        .order_by(AssistantMemory.id.desc())
    )
    items = query.all()
    if not term:
        return list(reversed(items))
    normalized = term.casefold()
    return [item for item in reversed(items) if normalized in item.value.casefold()]


def create_task(
    db: Session,
    tenant_id: int,
    chat: Chat,
    *,
    title: str,
    description: str | None = None,
    due_date: datetime | None = None,
) -> Task:
    task = Task(
        tenant_id=tenant_id,
        title=title[:255],
        description=(description or title)[:500],
        due_date=due_date,
        status="pending",
    )
    db.add(task)
    db.flush()

    ref_key = f"{_task_ref_key_prefix(chat)}{_slugify_key(title)}"
    task_ref = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id, AssistantMemory.key == ref_key)
        .first()
    )
    if not task_ref:
        task_ref = AssistantMemory(tenant_id=tenant_id, key=ref_key, value=str(task.id))
        db.add(task_ref)
    else:
        task_ref.value = str(task.id)

    return task


def list_tasks(db: Session, tenant_id: int, chat: Chat, *, include_completed: bool = False) -> list[Task]:
    refs = (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.key.like(f"{_task_ref_key_prefix(chat)}%"),
        )
        .order_by(AssistantMemory.id.desc())
        .all()
    )
    task_ids: list[int] = []
    for ref in refs:
        try:
            task_ids.append(int(ref.value.strip()))
        except (TypeError, ValueError):
            continue
    if not task_ids:
        return []

    tasks = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.id.in_(task_ids))
        .order_by(Task.created_at.asc())
        .all()
    )
    if include_completed:
        return tasks
    return [task for task in tasks if task.status not in {"completed", "cancelled", "done", "feito"}]


def create_reminder(
    db: Session,
    tenant_id: int,
    chat: Chat,
    *,
    title: str,
    remind_at: datetime,
    description: str | None = None,
) -> AgentReminder:
    reminder = AgentReminder(
        tenant_id=tenant_id,
        chat_id=chat.id,
        title=title[:255],
        description=(description or title)[:500],
        remind_at=remind_at,
        status="pending",
    )
    db.add(reminder)
    db.flush()
    return reminder


def list_reminders(db: Session, tenant_id: int, chat: Chat, *, include_sent: bool = False) -> list[AgentReminder]:
    query = (
        db.query(AgentReminder)
        .filter(AgentReminder.tenant_id == tenant_id, AgentReminder.chat_id == chat.id)
        .order_by(AgentReminder.remind_at.asc())
    )
    if include_sent:
        return query.all()
    return query.filter(AgentReminder.status.in_(["pending", "scheduled"])).all()


def create_appointment(
    db: Session,
    tenant_id: int,
    chat: Chat,
    *,
    title: str,
    scheduled_at: datetime,
    description: str | None = None,
) -> AgentAppointment:
    appointment = AgentAppointment(
        tenant_id=tenant_id,
        chat_id=chat.id,
        title=title[:255],
        description=(description or title)[:500],
        scheduled_at=scheduled_at,
        status="scheduled",
    )
    db.add(appointment)
    db.flush()
    return appointment


def list_appointments(db: Session, tenant_id: int, chat: Chat, *, include_cancelled: bool = False) -> list[AgentAppointment]:
    query = (
        db.query(AgentAppointment)
        .filter(AgentAppointment.tenant_id == tenant_id, AgentAppointment.chat_id == chat.id)
        .order_by(AgentAppointment.scheduled_at.asc())
    )
    if include_cancelled:
        return query.all()
    return query.filter(AgentAppointment.status != "cancelled").all()
