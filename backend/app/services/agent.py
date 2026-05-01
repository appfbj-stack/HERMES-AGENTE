import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AssistantMemory, Chat, ClientMemory, ClientProfile, ClientSkill, Lead, Message, Task, Tenant
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


CLIENT_SKILL_CATALOG: dict[str, dict[str, object]] = {
    "follow_up_automatico": {
        "nome_skill": "follow_up_automatico",
        "descricao": "Rotina para apoiar follow-ups recorrentes do cliente.",
        "configuracao": {"trigger": "followup", "mode": "suggested"},
    },
    "agenda_automatica": {
        "nome_skill": "agenda_automatica",
        "descricao": "Rotina para apoiar agendamentos frequentes do cliente.",
        "configuracao": {"trigger": "schedule", "mode": "suggested"},
    },
    "resposta_automatica_fora_do_horario": {
        "nome_skill": "resposta_automatica_fora_do_horario",
        "descricao": "Rotina de resposta assistida fora do horário padrão do cliente.",
        "configuracao": {"trigger": "off_hours", "mode": "suggested"},
    },
}


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


_WEEKDAY_MAP = {
    "segunda": 0,
    "segunda-feira": 0,
    "terca": 1,
    "terca-feira": 1,
    "terça": 1,
    "terça-feira": 1,
    "quarta": 2,
    "quarta-feira": 2,
    "quinta": 3,
    "quinta-feira": 3,
    "sexta": 4,
    "sexta-feira": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}


def _memory_key_prefix(chat: Chat) -> str:
    return f"chat:{chat.chat_external_id}:"


def _task_ref_key_prefix(chat: Chat) -> str:
    return f"taskref:{chat.chat_external_id}:"


def _task_notify_key_prefix(task_id: int) -> str:
    return f"tasknotify:{task_id}:"


def _is_internal_memory_key(key: str) -> bool:
    return key.startswith("taskref:") or key.startswith("tasknotify:")


def _load_json_blob(raw_value: str | None) -> object | None:
    if not raw_value:
        return None
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def _dump_json_blob(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _get_client_memory_record(db: Session, tenant_id: int, tipo: str, chave: str) -> ClientMemory | None:
    return (
        db.query(ClientMemory)
        .filter(ClientMemory.tenant_id == tenant_id, ClientMemory.tipo == tipo, ClientMemory.chave == chave)
        .first()
    )


def _upsert_client_memory(db: Session, tenant_id: int, tipo: str, chave: str, value: object) -> ClientMemory:
    record = _get_client_memory_record(db, tenant_id, tipo, chave)
    payload = _dump_json_blob(value)
    if not record:
        record = ClientMemory(tenant_id=tenant_id, tipo=tipo, chave=chave, valor=payload)
        db.add(record)
        db.flush()
    else:
        record.valor = payload
    return record


def _increment_client_counter(db: Session, tenant_id: int, tipo: str, chave: str) -> int:
    record = _get_client_memory_record(db, tenant_id, tipo, chave)
    current_value = _load_json_blob(record.valor) if record else None
    if not isinstance(current_value, dict):
        current_value = {"count": 0}
    count = int(current_value.get("count", 0)) + 1
    current_value["count"] = count
    _upsert_client_memory(db, tenant_id, tipo, chave, current_value)
    return count


def _has_active_client_skill(db: Session, tenant_id: int, nome_skill: str) -> bool:
    return (
        db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == tenant_id, ClientSkill.nome_skill == nome_skill, ClientSkill.ativa.is_(True))
        .first()
        is not None
    )


def _find_client_skill(db: Session, tenant_id: int, nome_skill: str) -> ClientSkill | None:
    return (
        db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == tenant_id, ClientSkill.nome_skill == nome_skill)
        .first()
    )


def _emit_client_suggestion_once(
    db: Session,
    tenant_id: int,
    suggestion_key: str,
    suggestion_text: str,
) -> str | None:
    if _has_active_client_skill(db, tenant_id, suggestion_key):
        return None
    marker = _get_client_memory_record(db, tenant_id, "insight", f"suggestion:{suggestion_key}")
    if marker is not None:
        return None
    _upsert_client_memory(
        db,
        tenant_id,
        "insight",
        f"suggestion:{suggestion_key}",
        {"suggested_at": _utcnow().isoformat(), "message": suggestion_text},
    )
    return suggestion_text


def _detect_explicit_skill_activation(inbound_text: str) -> str | None:
    normalized = _normalize_text(inbound_text)
    if not any(token in normalized for token in ("ative", "ativar", "pode ativar", "quero ativar", "confirmo")):
        return None

    if "follow" in normalized or "follow-up" in normalized or "follow up" in normalized:
        return "follow_up_automatico"
    if "agenda" in normalized or "agendar" in normalized or "reuniao" in normalized or "reunião" in normalized:
        return "agenda_automatica"
    if "resposta automatica" in normalized or "resposta automática" in normalized or "fora do horario" in normalized or "fora do horário" in normalized:
        return "resposta_automatica_fora_do_horario"
    return None


def maybe_activate_client_skill(db: Session, tenant_id: int, inbound_text: str) -> str | None:
    skill_key = _detect_explicit_skill_activation(inbound_text)
    if not skill_key:
        return None

    catalog_entry = CLIENT_SKILL_CATALOG.get(skill_key)
    if not catalog_entry:
        return None

    skill = _find_client_skill(db, tenant_id, skill_key)
    if not skill:
        skill = ClientSkill(
            tenant_id=tenant_id,
            nome_skill=str(catalog_entry["nome_skill"]),
            descricao=str(catalog_entry["descricao"]),
            ativa=True,
            configuracao=_dump_json_blob(catalog_entry["configuracao"]),
        )
        db.add(skill)
    else:
        skill.descricao = str(catalog_entry["descricao"])
        skill.ativa = True
        skill.configuracao = _dump_json_blob(catalog_entry["configuracao"])

    _upsert_client_memory(
        db,
        tenant_id,
        "insight",
        f"activation:{skill_key}",
        {"activated_at": _utcnow().isoformat(), "skill": skill_key},
    )
    return f"✅ Skill ativada com sua confirmação: {skill_key}"


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
    normalized = _normalize_text(text)
    now = _utcnow()

    relative_match = re.search(r"\bdaqui\s+(\d+)\s+(minuto|minutos|hora|horas|dia|dias)\b", normalized)
    if relative_match:
        amount, unit = relative_match.groups()
        value = int(amount)
        if "minuto" in unit:
            return now + timedelta(minutes=value)
        if "hora" in unit:
            return now + timedelta(hours=value)
        return now + timedelta(days=value)

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

    hour_match = re.search(r"\b(?:as|às)?\s*(\d{1,2})h(?:\s*(\d{2}))?\b", normalized)
    explicit_time = None
    if hour_match:
        hour, minute = hour_match.groups()
        explicit_time = (int(hour), int(minute or 0))

    time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if time_match:
        hour, minute = time_match.groups()
        candidate = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
        if candidate < now:
            candidate = candidate + timedelta(days=1)
        return candidate

    if explicit_time is None:
        compact_match = re.search(r"\b(?:as|às)\s+(\d{1,2})\b", normalized)
        if compact_match:
            explicit_time = (int(compact_match.group(1)), 0)

    if "amanha" in normalized:
        hour, minute = explicit_time or (9, 0)
        return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)

    if "hoje" in normalized:
        hour, minute = explicit_time or (now.hour, now.minute)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate < now:
            candidate = candidate + timedelta(days=1)
        return candidate

    weekday_match = re.search(
        r"\b(segunda-feira|terca-feira|terça-feira|quarta-feira|quinta-feira|sexta-feira|sabado|sábado|domingo|segunda|terca|terça|quarta|quinta|sexta)\b",
        normalized,
    )
    if weekday_match:
        weekday_name = weekday_match.group(1)
        target_weekday = _WEEKDAY_MAP.get(weekday_name)
        if target_weekday is not None:
            days_ahead = (target_weekday - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            hour, minute = explicit_time or (9, 0)
            return (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)

    if explicit_time is not None:
        hour, minute = explicit_time
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
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

    candidate = re.sub(
        r"\b(?:hoje|amanh[aã]|depois|às|as|segunda(?:-feira)?|ter[cç]a(?:-feira)?|quarta(?:-feira)?|quinta(?:-feira)?|sexta(?:-feira)?|s[áa]bado|domingo|daqui)\b.*$",
        "",
        candidate,
        flags=re.IGNORECASE,
    ).strip(" .:-")
    if not candidate:
        candidate = text[:120].strip()
    return candidate[:120] or "Tarefa automática"


def _format_due_date(value: datetime | None) -> str:
    if value is None:
        return "sem data"
    return value.strftime("%d/%m/%Y %H:%M")


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
    tenant_memory = [item for item in memory if not item.key.startswith(prefix) and not _is_internal_memory_key(item.key)]

    chat_memory_text = "\n".join(f"- {item.value}" for item in reversed(chat_memory[-8:])) or "Nenhuma memória desta conversa."
    tenant_memory_text = "\n".join(f"- {item.key}: {item.value}" for item in reversed(tenant_memory[-10:])) or "Nenhuma memória geral do tenant."

    client_profile = db.query(ClientProfile).filter(ClientProfile.tenant_id == tenant_id).first()
    client_profile_lines: list[str] = []
    if client_profile:
        if client_profile.tipo_negocio:
            client_profile_lines.append(f"- Tipo de negócio: {client_profile.tipo_negocio}")
        if client_profile.objetivo:
            client_profile_lines.append(f"- Objetivo: {client_profile.objetivo}")
        if client_profile.horario_funcionamento:
            client_profile_lines.append(f"- Horário: {client_profile.horario_funcionamento}")
        if client_profile.preferencias:
            client_profile_lines.append(f"- Preferências: {client_profile.preferencias}")
        client_profile_lines.append(f"- Nível de automação: {client_profile.nivel_automacao}")
    client_profile_text = "\n".join(client_profile_lines) or "Nenhum perfil estratégico do cliente cadastrado."

    client_memory_items = (
        db.query(ClientMemory)
        .filter(ClientMemory.tenant_id == tenant_id)
        .order_by(ClientMemory.updated_at.desc())
        .limit(12)
        .all()
    )
    client_memory_lines: list[str] = []
    for item in reversed(client_memory_items):
        parsed = _load_json_blob(item.valor)
        if item.tipo == "comportamento" and isinstance(parsed, dict) and "count" in parsed:
            client_memory_lines.append(f"- {item.tipo}/{item.chave}: observado {parsed['count']} vez(es)")
        elif item.tipo == "preferencia":
            client_memory_lines.append(f"- {item.tipo}/{item.chave}: {parsed}")
        elif item.tipo == "insight" and isinstance(parsed, dict) and "message" in parsed:
            client_memory_lines.append(f"- sugestão registrada: {parsed['message']}")
    client_memory_text = "\n".join(client_memory_lines) or "Nenhuma memória estratégica do tenant."

    active_client_skills = (
        db.query(ClientSkill)
        .filter(ClientSkill.tenant_id == tenant_id, ClientSkill.ativa.is_(True))
        .order_by(ClientSkill.created_at.desc())
        .limit(8)
        .all()
    )
    active_client_skills_text = (
        "\n".join(f"- {item.nome_skill}: {item.descricao or 'Skill ativa'}" for item in active_client_skills)
        or "Nenhuma skill automática ativa para este cliente."
    )

    # Bloco CRM (vazio se CRM inativo ou lead não encontrado)
    crm_block = build_crm_context_block(db, tenant_id, lead)

    system_content = (
        f"{base_prompt}\n\n"
        f"Perfil estratégico do cliente:\n{client_profile_text}\n\n"
        f"Aprendizados estratégicos do tenant:\n{client_memory_text}\n\n"
        f"Skills ativas do cliente:\n{active_client_skills_text}\n\n"
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


def maybe_create_task(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> Task | None:
    """Cria tarefa automática se houver palavras-chave de compromisso."""
    text = _normalize_text(inbound_text)
    triggers = ["ligar", "retornar", "agendar", "reuniao", "orcamento", "me lembre", "lembrar", "tarefa"]
    if not any(item in text for item in triggers):
        return

    title = _extract_task_title(inbound_text)
    ref_key = f"{_task_ref_key_prefix(chat)}{_slugify(title)}"
    task_ref = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id, AssistantMemory.key == ref_key)
        .first()
    )
    if task_ref:
        try:
            task_id = int(task_ref.value.strip())
        except (TypeError, ValueError):
            task_id = None
        if task_id:
            existing_task = (
                db.query(Task)
                .filter(Task.id == task_id, Task.tenant_id == tenant_id, Task.status.in_(["pending", "open", "pendente"]))
                .first()
            )
            if existing_task:
                return None

    task = Task(
        tenant_id=tenant_id,
        title=title,
        description=inbound_text[:500],
        due_date=_extract_due_date(inbound_text),
        status="pending",
    )
    db.add(task)
    db.flush()

    if not task_ref:
        task_ref = AssistantMemory(tenant_id=tenant_id, key=ref_key, value=str(task.id))
        db.add(task_ref)
    else:
        task_ref.value = str(task.id)
    return task


def observe_client_patterns(db: Session, tenant_id: int, inbound_text: str) -> list[str]:
    normalized = _normalize_text(inbound_text)
    suggestions: list[str] = []

    if any(token in normalized for token in ("follow-up", "follow up", "followup", "retorno", "retornar")):
        count = _increment_client_counter(db, tenant_id, "comportamento", "followup_mentions")
        if count >= 3:
            suggestion = _emit_client_suggestion_once(
                db,
                tenant_id,
                "follow_up_automatico",
                "💡 Sugestão: percebi muitos follow-ups. Posso criar uma rotina de follow-up automático se você confirmar.",
            )
            if suggestion:
                suggestions.append(suggestion)

    if any(token in normalized for token in ("agendar", "agenda", "reuniao", "reunião", "seminario", "seminário", "horario", "horário")):
        count = _increment_client_counter(db, tenant_id, "comportamento", "scheduling_mentions")
        if count >= 3:
            suggestion = _emit_client_suggestion_once(
                db,
                tenant_id,
                "agenda_automatica",
                "💡 Sugestão: percebi muitos agendamentos. Posso criar uma rotina de agenda automática se você confirmar.",
            )
            if suggestion:
                suggestions.append(suggestion)

    if any(token in normalized for token in ("respondo tarde", "respondo a noite", "respondo à noite", "so vejo depois", "só vejo depois", "atendo a noite", "atendo à noite")):
        _upsert_client_memory(db, tenant_id, "preferencia", "horario_resposta", {"periodo": "noite"})
        suggestion = _emit_client_suggestion_once(
            db,
            tenant_id,
            "resposta_automatica_fora_do_horario",
            "💡 Sugestão: notei que você costuma responder mais tarde. Posso preparar uma rotina de resposta automática fora do horário, se você confirmar.",
        )
        if suggestion:
            suggestions.append(suggestion)

    return suggestions


def process_inbound_automation(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> list[str]:
    confirmations: list[str] = []

    memory = maybe_save_memory(db, tenant_id, chat, inbound_text)
    if memory is not None:
        confirmations.append(f"✅ Salvo na memória: {_truncate(memory.value, 80)}")

    task = maybe_create_task(db, tenant_id, chat, inbound_text)
    if task is not None:
        confirmations.append(f"✅ Tarefa criada: {task.title}")

    activation = maybe_activate_client_skill(db, tenant_id, inbound_text)
    if activation is not None:
        confirmations.append(activation)

    confirmations.extend(observe_client_patterns(db, tenant_id, inbound_text))

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


def maybe_handle_task_query(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> str | None:
    normalized = _normalize_text(inbound_text)
    if not normalized:
        return None

    is_task_query = any(
        token in normalized
        for token in (
            "quais tarefas",
            "quais lembretes",
            "quais sao minhas tarefas",
            "quais sao meus lembretes",
            "o que esta agendado",
            "o que tenho agendado",
            "tenho alguma tarefa",
            "tenho algum lembrete",
            "meus lembretes",
            "minhas tarefas",
            "tarefas pendentes",
            "lembretes pendentes",
        )
    )
    if not is_task_query:
        return None

    refs = (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.key.like(f"{_task_ref_key_prefix(chat)}%"),
        )
        .order_by(AssistantMemory.id.desc())
        .all()
    )
    if not refs:
        return "Ainda não encontrei tarefas ou lembretes salvos para esta conversa."

    task_ids: list[int] = []
    for ref in refs:
        try:
            task_ids.append(int(ref.value.strip()))
        except (TypeError, ValueError):
            continue
    if not task_ids:
        return "Ainda não encontrei tarefas ou lembretes salvos para esta conversa."

    tasks = (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id, Task.id.in_(task_ids))
        .order_by(Task.created_at.asc())
        .all()
    )
    active_tasks = [task for task in tasks if task.status not in {"completed", "cancelled", "done", "feito"}]
    if not active_tasks:
        return "As tarefas e lembretes desta conversa já foram concluídos ou não estão mais pendentes."

    lines = ["📋 Tarefas e lembretes desta conversa:"]
    for task in active_tasks[-8:]:
        lines.append(f"- {task.title} ({_format_due_date(task.due_date)})")
    return "\n".join(lines)


def find_task_refs(db: Session, tenant_id: int, task_id: int) -> list[AssistantMemory]:
    return (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.value == str(task_id),
            AssistantMemory.key.like("taskref:%"),
        )
        .all()
    )


def task_reminder_already_sent(db: Session, tenant_id: int, task_id: int) -> bool:
    return (
        db.query(AssistantMemory)
        .filter(
            AssistantMemory.tenant_id == tenant_id,
            AssistantMemory.key.like(f"{_task_notify_key_prefix(task_id)}%"),
        )
        .first()
        is not None
    )


def mark_task_reminder_sent(db: Session, tenant_id: int, task_id: int, scope: str) -> None:
    key = f"{_task_notify_key_prefix(task_id)}{scope}"
    marker = (
        db.query(AssistantMemory)
        .filter(AssistantMemory.tenant_id == tenant_id, AssistantMemory.key == key)
        .first()
    )
    timestamp = _utcnow().isoformat()
    if not marker:
        marker = AssistantMemory(tenant_id=tenant_id, key=key, value=timestamp)
        db.add(marker)
    else:
        marker.value = timestamp


def maybe_create_lead(db: Session, tenant_id: int, chat: Chat, inbound_text: str) -> None:
    """Delega ao CRM (cria/vincula lead pelo telefone) se o módulo estiver ativo.

    Importação local evita ciclo agent <-> crm_agent.
    """
    from app.services.crm_agent import get_or_create_lead_from_chat
    get_or_create_lead_from_chat(db, tenant_id, chat, inbound_text)
