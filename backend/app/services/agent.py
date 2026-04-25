from sqlalchemy.orm import Session

from app.models import AssistantMemory, Chat, Lead, Message, Task


SYSTEM_PROMPT = """
Você é um assistente de negócios.
Você deve responder clientes, captar leads, organizar informações, criar tarefas,
sugerir ações e manter contexto do cliente.
Responda de forma útil, objetiva e comercialmente clara.
""".strip()


def build_context(db: Session, tenant_id: int, chat: Chat) -> list[dict[str, str]]:
    messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).limit(20).all()
    memory = db.query(AssistantMemory).filter(AssistantMemory.tenant_id == tenant_id).all()

    memory_text = "\n".join(f"{item.key}: {item.value}" for item in memory) or "Sem memória adicional."
    context: list[dict[str, str]] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nMemória do tenant:\n{memory_text}"}
    ]

    role_map = {"user": "user", "assistant": "assistant", "human": "assistant"}
    for item in messages:
        context.append({"role": role_map.get(item.sender_type, "user"), "content": item.content})
    return context


def maybe_create_lead(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> None:
    if len(inbound_text.strip()) < 10:
        return

    existing = db.query(Lead).filter(Lead.tenant_id == tenant_id, Lead.phone == chat.contact_phone).first()
    if existing:
        return

    lead = Lead(
        tenant_id=tenant_id,
        name=chat.contact_name or f"Contato {chat.chat_external_id}",
        phone=chat.contact_phone,
        interest=inbound_text[:255],
        status="new",
    )
    db.add(lead)


def maybe_create_task(db: Session, tenant_id: int, inbound_text: str) -> None:
    text = inbound_text.lower()
    triggers = ["ligar", "retornar", "agendar", "reunião", "orcamento", "orçamento"]
    if not any(item in text for item in triggers):
        return

    task = Task(
        tenant_id=tenant_id,
        title="Follow-up automático",
        description=inbound_text[:500],
        status="pending",
    )
    db.add(task)

