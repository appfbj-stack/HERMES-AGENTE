from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AssistantMemory, Chat, Lead, Message, Task, Tenant


DEFAULT_SYSTEM_PROMPT = """
Você é um assistente de negócios.
Você deve responder clientes, captar leads, organizar informações, criar tarefas,
sugerir ações e manter contexto do cliente.
Responda de forma útil, objetiva e comercialmente clara.
SEJA BREVE: respostas devem ter no máximo 3-4 parágrafos curtos. Não use floreios desnecessários.
""".strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def build_context(db: Session, tenant_id: int, chat: Chat) -> list[dict[str, str]]:
    settings = get_settings()
    # Limita histórico: pega só as N últimas mensagens (em vez de todas)
    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.desc())
        .limit(settings.max_context_messages)
        .all()
    )
    messages.reverse()  # cronológico de novo

    memory = db.query(AssistantMemory).filter(AssistantMemory.tenant_id == tenant_id).all()

    # Usa o system_prompt customizado do tenant se houver, senão default
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    base_prompt = (tenant.system_prompt if tenant and tenant.system_prompt else DEFAULT_SYSTEM_PROMPT)

    memory_text = "\n".join(f"{item.key}: {item.value}" for item in memory) or "Sem memória adicional."
    context: list[dict[str, str]] = [
        {"role": "system", "content": f"{base_prompt}\n\nMemória do tenant:\n{memory_text}"}
    ]

    role_map = {"user": "user", "assistant": "assistant", "human": "assistant"}
    for item in messages:
        # Trunca cada mensagem do histórico pra economizar tokens
        truncated = _truncate(item.content, settings.max_context_chars_per_message)
        context.append({"role": role_map.get(item.sender_type, "user"), "content": truncated})
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

