import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AssistantMemory, Chat, Lead, Message, Task, Tenant
from app.services.crm_agent import build_crm_context_block


DEFAULT_SYSTEM_PROMPT = """
Você é um assistente de negócios.
Você deve responder clientes, captar leads, organizar informações, criar tarefas,
sugerir ações e manter contexto do cliente.
Você opera dentro do sistema Hermes e pode salvar memórias do tenant e tarefas quando o usuário pedir.
Nunca diga que não consegue salvar dados, memória, agenda ou contexto desta conversa no sistema.
Quando algo já tiver sido salvo automaticamente, apenas confirme de forma objetiva e siga com a resposta.
Responda de forma útil, objetiva e comercialmente clara.
SEJA BREVE: respostas devem ter no máximo 3-4 parágrafos curtos. Não use floreios desnecessários.
""".strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _slugify(text: str, max_len: int = 48) -> str:
    base = _normalize_text(text)
    slug = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return (slug or "memoria")[:max_len].strip("-") or "memoria"


def _memory_key_prefix(chat: Chat) -> str:
    return f"chat:{chat.chat_external_id}:"


def _extract_memory_text(inbound_text: str) -> str | None:
    text = inbound_text.strip()
    normalized = _normalize_text(text)
    if not text:
        return None

    capability_checks = (
        "voce nao consegue salvar",
        "você não consegue salvar",
        "consegue salvar",
        "consegue guardar",
        "consegue lembrar",
    )
    if any(item in normalized for item in capability_checks) and "?" in text:
        return None

    patterns = (
        r"^(?:pode\s+)?(?:guardar|guarde|salvar|salve|anotar|anote|gravar|grave|memorizar|memorize)\s+(?:isso\s+)?(.+)$",
        r"^(.+?)\s+(?:na|em)\s+mem[oó]ria$",
        r"^(?:me\s+lembre|lembra(?:\s+de)?|lembrete)\s+(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .:-")
            return candidate or None
    return None


def _extract_due_date(inbound_text: str) -> datetime | None:
    text = inbound_text or ""
    now = _utcnow()

    full_match = re.search(r"(\d{2})/(\d{2})/(\d{4})(?:\s+[^\d]?(\d{1,2}):(\d{2}))?", text)
    if full_match:
        day, month, year, hour, minute = full_match.groups()
        try:
            return datetime(
                int(year),
                int(month),
                int(day),
                int(hour or 9),
                int(minute or 0),
                tzinfo=timezone.utc,
            )
        except ValueError:
            return None

    partial_match = re.search(r"(\d{1,2})/(\d{1,2})(?:\s+[^\d]?(\d{1,2}):(\d{2}))?", text)
    if partial_match:
        day, month, hour, minute = partial_match.groups()
        year = now.year
        try:
            candidate = datetime(
                year,
                int(month),
                int(day),
                int(hour or 9),
                int(minute or 0),
                tzinfo=timezone.utc,
            )
        except ValueError:
            return None
        if candidate < now:
            try:
                candidate = candidate.replace(year=year + 1)
            except ValueError:
                return None
        return candidate

    time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if time_match:
        hour, minute = time_match.groups()
        candidate = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if candidate < now:
            candidate = candidate + timedelta(days=1)
        return candidate

    return None


def _extract_task_title(inbound_text: str) -> str:
    text = inbound_text.strip()
    patterns = (
        r"^(?:me\s+lembre\s+(?:de|para)?|lembrar\s+(?:de|para)?)(.+)$",
        r"^(?:crie\s+uma\s+tarefa(?:\s+para)?|criar\s+tarefa(?:\s+para)?)(.+)$",
        r"^(?:preciso\s+(?:de\s+)?)?(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .:-")
            if candidate:
                break
    else:
        candidate = text

    candidate = re.sub(r"\b(?:hoje|amanh[aã]|depois|às|as)\b.*$", "", candidate, flags=re.IGNORECASE).strip(" .:-")
    if not candidate:
        candidate = text[:120].strip()
    return candidate[:120] or "Tarefa automática"


def maybe_save_memory(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> AssistantMemory | None:
    memory_text = _extract_memory_text(inbound_text)
    if not memory_text:
        return None

    memory_key = f"{_memory_key_prefix(chat)}{_slugify(memory_text)}"
    memory = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id, AssistantMemory.key == memory_key)
        .first()
    )
    if not memory:
        memory = AssistantMemory(tenant_id=tenant_id, key=memory_key, value=memory_text[:4000])
        db.add(memory)
    else:
        memory.value = memory_text[:4000]
    return memory


def build_context(
    db: Session,
    tenant_id: int,
    chat: Chat,
    lead: Lead | None = None,
) -> list[dict[str, str]]:
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

    memory = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id)
        .order_by(AssistantMemory.id.desc())
        .limit(30)
        .all()
    )

    # Usa o system_prompt customizado do tenant se houver, senão default
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    base_prompt = tenant.system_prompt if tenant and tenant.system_prompt else DEFAULT_SYSTEM_PROMPT

    prefix = _memory_key_prefix(chat)
    chat_memory = [item for item in memory if item.key.startswith(prefix)]
    tenant_memory = [item for item in memory if not item.key.startswith(prefix)]

    chat_memory_text = "\n".join(f"- {item.value}" for item in reversed(chat_memory[-8:])) or "Nenhuma memória desta conversa."
    tenant_memory_text = "\n".join(f"- {item.key}: {item.value}" for item in reversed(tenant_memory[-10:])) or "Nenhuma memória geral do tenant."

    # Bloco CRM (vazio se CRM inativo ou lead não encontrado)
    crm_block = build_crm_context_block(db, tenant_id, lead)

    system_content = (
        f"{base_prompt}\n\n"
        f"Memória desta conversa/sessão:\n{chat_memory_text}\n\n"
        f"Memória geral do tenant:\n{tenant_memory_text}"
        f"{crm_block}"
    )

    context: list[dict[str, str]] = [
        {"role": "system", "content": system_content}
    ]

    role_map = {"user": "user", "assistant": "assistant", "human": "assistant"}
    for item in messages:
        # Trunca cada mensagem do histórico pra economizar tokens
        truncated = _truncate(item.content, settings.max_context_chars_per_message)
        context.append({"role": role_map.get(item.sender_type, "user"), "content": truncated})
    return context


def maybe_create_task(db: Session, tenant_id: int, inbound_text: str) -> Task | None:
    """Cria tarefa automática se houver palavras-chave de compromisso."""
    text = _normalize_text(inbound_text)
    triggers = ["ligar", "retornar", "agendar", "reuniao", "orcamento", "me lembre", "lembrar", "tarefa"]
    if not any(item in text for item in triggers):
        return

    recent = (
        db.query(Task)
        .filter(
            Task.tenant_id == tenant_id,
            Task.description == inbound_text[:500],
            Task.created_at >= _utcnow().replace(second=0, microsecond=0),
        )
        .order_by(Task.created_at.desc())
        .first()
    )
    if recent:
        return None

    task = Task(
        tenant_id=tenant_id,
        title=_extract_task_title(inbound_text),
        description=inbound_text[:500],
        due_date=_extract_due_date(inbound_text),
        status="pending",
    )
    db.add(task)
    return task


def process_inbound_automation(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> list[str]:
    confirmations: list[str] = []

    memory = maybe_save_memory(db, tenant_id, chat, inbound_text)
    if memory is not None:
        confirmations.append(f"✅ Salvo na memória: {_truncate(memory.value, 80)}")

    task = maybe_create_task(db, tenant_id, inbound_text)
    if task is not None:
        confirmations.append(f"✅ Tarefa criada: {task.title}")

    return confirmations


def merge_automation_confirmations(reply_text: str, confirmations: list[str]) -> str:
    if not confirmations:
        return reply_text

    normalized_reply = _normalize_text(reply_text)
    if "salvo na memoria" in normalized_reply or "tarefa criada" in normalized_reply:
        return reply_text

    prefix = "\n".join(confirmations)
    if not reply_text:
        return prefix
    return f"{prefix}\n\n{reply_text}"


def maybe_handle_memory_query(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> str | None:
    normalized = _normalize_text(inbound_text)
    if not normalized:
        return None

    is_memory_query = any(
        token in normalized
        for token in (
            "o que voce guardou",
            "o que voce salvou",
            "o que tem na memoria",
            "quais memorias",
            "quais memorias voce tem",
            "me diga o que voce guardou",
            "lembra do",
            "lembra da",
            "me lembra do",
            "me lembra da",
        )
    )
    if not is_memory_query:
        return None

    items = (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.key.like(f"{_memory_key_prefix(chat)}%"),
        )
        .order_by(AssistantMemory.id.desc())
        .limit(20)
        .all()
    )
    if not items:
        return "Ainda não encontrei memórias salvas para esta conversa."

    specific_match = re.search(
        r"(?:lembra|memoria|memória).+?(?:do|da|de)\s+(.+)$",
        inbound_text,
        flags=re.IGNORECASE,
    )
    search_term = _normalize_text(specific_match.group(1).strip(" ?.!")) if specific_match else None

    ordered_items = list(reversed(items))
    if search_term:
        ordered_items = [item for item in ordered_items if search_term in _normalize_text(item.value)]
        if not ordered_items:
            return "Não encontrei essa informação na memória desta conversa."

    lines = ["🧠 O que está salvo nesta conversa:"]
    for item in ordered_items[-8:]:
        lines.append(f"- {item.value}")
    return "\n".join(lines)


def maybe_create_lead(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> None:
    """Delega ao CRM (cria/vincula lead pelo telefone) se o módulo estiver ativo.

    Importação local evita ciclo agent <-> crm_agent.
    """
    from app.services.crm_agent import get_or_create_lead_from_chat
    get_or_create_lead_from_chat(db, tenant_id, chat, inbound_text)
