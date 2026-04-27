"""
CRM ↔ Hermes Integration Service

Responsabilidades:
  1. get_or_create_lead_from_chat()  — busca/cria lead pelo telefone e vincula ao chat
  2. build_crm_context_block()       — gera bloco de texto CRM pra injetar no system prompt
  3. parse_and_execute_crm_commands()— extrai [[CRM:...]] da resposta, executa e limpa o texto
  4. update_lead_last_contact()      — atualiza last_contact_at do lead

Comandos CRM (incluídos pelo Hermes ao final da resposta):
  [[CRM:status <new|contacted|qualified|proposal|closed|lost>]]
  [[CRM:interest "<texto curto>"]]]
  [[CRM:note "<observação interna>"]]
  [[CRM:followup "<título>" <YYYY-MM-DDTHH:MM>]]
  [[CRM:kanban <nome_parcial_da_coluna>]]

Todos os comandos são REMOVIDOS da resposta antes de enviá-la ao cliente.
"""
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Chat, CrmActivityLog, CrmFollowup, CrmKanbanColumn, Lead, TenantModule

# ─── Constantes ───────────────────────────────────────────────────────────────

STATUS_VALID = {"new", "contacted", "qualified", "proposal", "closed", "lost"}

_CRM_CMD_RE = re.compile(
    r"\[\[CRM:(\w+)\s*(.*?)\]\]",
    re.DOTALL | re.IGNORECASE,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_crm_active(db: Session, tenant_id: int) -> bool:
    mod = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    return bool(mod and mod.crm)


def _log(db: Session, tenant_id: int, lead_id: int, action: str, detail: str) -> None:
    db.add(CrmActivityLog(
        tenant_id=tenant_id,
        lead_id=lead_id,
        action=action,
        detail=detail,
    ))


# ─── 1. Buscar / criar lead e vincular ao chat ────────────────────────────────

def get_or_create_lead_from_chat(
    db: Session,
    tenant_id: int,
    chat: Chat,
    inbound_text: str,
) -> Lead | None:
    """
    Encontra o lead pelo telefone ou cria um novo.
    Vincula chat.lead_id ao lead encontrado/criado.
    Só executa se o módulo CRM estiver ativo.
    Retorna o lead ou None se CRM inativo.
    """
    if not _is_crm_active(db, tenant_id):
        return None

    # Ignora mensagens de início sem conteúdo útil
    if inbound_text.strip() in {"/start", ""}:
        return None

    # Busca por phone (identificador mais confiável)
    lead: Lead | None = None
    if chat.contact_phone:
        lead = (
            db.query(Lead)
            .filter(Lead.tenant_id == tenant_id, Lead.phone == chat.contact_phone)
            .first()
        )

    # Se não achou por phone, tenta pelo lead_id já vinculado ao chat
    if not lead and chat.lead_id:
        lead = db.query(Lead).filter(Lead.id == chat.lead_id, Lead.tenant_id == tenant_id).first()

    # Cria lead se não existir
    if not lead:
        # Primeira coluna do kanban deste tenant (se houver)
        first_col = (
            db.query(CrmKanbanColumn)
            .filter(CrmKanbanColumn.tenant_id == tenant_id)
            .order_by(CrmKanbanColumn.position.asc())
            .first()
        )
        lead = Lead(
            tenant_id=tenant_id,
            name=chat.contact_name or f"Contato {chat.chat_external_id[:12]}",
            phone=chat.contact_phone,
            interest=inbound_text[:255] if len(inbound_text) > 5 else None,
            status="new",
            origem=chat.channel,   # whatsapp | telegram
            kanban_column_id=first_col.id if first_col else None,
        )
        db.add(lead)
        db.flush()  # gera lead.id
        _log(db, tenant_id, lead.id, "lead_created_auto",
             f"Criado automaticamente via {chat.channel}: {chat.contact_phone}")

    # Vincula chat ↔ lead (idempotente)
    if chat.lead_id != lead.id:
        chat.lead_id = lead.id

    # Atualiza last_contact_at
    lead.last_contact_at = _utcnow()
    lead.updated_at = _utcnow()

    return lead


# ─── 2. Bloco de contexto CRM para o system prompt ───────────────────────────

def build_crm_context_block(db: Session, tenant_id: int, lead: Lead | None) -> str:
    """
    Retorna um bloco de texto CRM para ser injetado ao final do system prompt.
    Inclui dados do lead + follow-ups pendentes de hoje + instruções de comandos.
    """
    if not lead:
        return ""

    status_label = {
        "new": "Novo", "contacted": "Contactado", "qualified": "Qualificado",
        "proposal": "Proposta enviada", "closed": "Fechado", "lost": "Perdido",
    }.get(lead.status, lead.status)

    # Follow-ups de hoje pendentes
    today_start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = _utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    followups_hoje = (
        db.query(CrmFollowup)
        .filter(
            CrmFollowup.lead_id == lead.id,
            CrmFollowup.data_hora >= today_start,
            CrmFollowup.data_hora <= today_end,
            CrmFollowup.status == "pendente",
        )
        .all()
    )

    # Kanban column name
    kanban_name = "—"
    if lead.kanban_column_id:
        col = db.query(CrmKanbanColumn).filter(CrmKanbanColumn.id == lead.kanban_column_id).first()
        if col:
            kanban_name = col.name

    # Todas as colunas disponíveis (para o comando kanban)
    all_cols = (
        db.query(CrmKanbanColumn)
        .filter(CrmKanbanColumn.tenant_id == tenant_id)
        .order_by(CrmKanbanColumn.position)
        .all()
    )
    cols_list = " | ".join(f'"{c.name}"' for c in all_cols) if all_cols else "(nenhuma configurada)"

    followup_lines = "\n".join(
        f"  - {fu.titulo} às {fu.data_hora.strftime('%H:%M') if hasattr(fu.data_hora, 'strftime') else fu.data_hora}"
        for fu in followups_hoje
    ) or "  (nenhum hoje)"

    block = f"""
=== DADOS DO LEAD (CRM) ===
Nome: {lead.name}
Telefone: {lead.phone or "—"}
Email: {lead.email or "—"}
Status CRM: {status_label}
Kanban: {kanban_name}
Interesse: {lead.interest or "—"}
Observações: {lead.observacoes or "—"}
Follow-ups hoje:
{followup_lines}

=== AÇÕES CRM (opcional — use no FINAL da resposta, invisível ao cliente) ===
Você pode atualizar o CRM incluindo comandos ao final da sua resposta.
Os comandos são removidos antes de enviar ao cliente.

Comandos disponíveis:
  [[CRM:status <new|contacted|qualified|proposal|closed|lost>]]
  [[CRM:interest "<interesse do lead>"]]
  [[CRM:note "<observação interna>"]]
  [[CRM:followup "<título>" <YYYY-MM-DDTHH:MM>]]
  [[CRM:kanban "<nome da coluna>"]]  — colunas: {cols_list}

Exemplos:
  [[CRM:status contacted]] [[CRM:interest "Plano Pro mensal"]]
  [[CRM:followup "Ligar para fechar proposta" 2025-05-10T14:00]]

Use os comandos SOMENTE se houver informação nova e relevante para registrar.
===========================""".strip()

    return "\n\n" + block


# ─── 3. Parsear e executar comandos [[CRM:...]] ───────────────────────────────

def parse_and_execute_crm_commands(
    db: Session,
    tenant_id: int,
    lead: Lead | None,
    reply_text: str,
) -> str:
    """
    Extrai todos os [[CRM:...]] do reply_text, executa as ações no banco,
    e retorna o texto limpo (sem os comandos).
    Seguro: erros em comandos individuais não interrompem os demais.
    """
    if not lead:
        # Remove comandos mesmo sem lead (não vaza texto esquisito para o cliente)
        return _CRM_CMD_RE.sub("", reply_text).strip()

    commands = _CRM_CMD_RE.findall(reply_text)
    cleaned = _CRM_CMD_RE.sub("", reply_text).strip()

    for cmd, args in commands:
        cmd = cmd.lower().strip()
        args = args.strip().strip('"').strip("'")

        try:
            if cmd == "status":
                _cmd_status(db, tenant_id, lead, args)
            elif cmd == "interest":
                _cmd_interest(db, tenant_id, lead, args)
            elif cmd == "note":
                _cmd_note(db, tenant_id, lead, args)
            elif cmd == "followup":
                _cmd_followup(db, tenant_id, lead, args)
            elif cmd == "kanban":
                _cmd_kanban(db, tenant_id, lead, args)
        except Exception as exc:  # noqa: BLE001
            print(f"[crm_agent] command [[CRM:{cmd} {args}]] failed: {exc}")

    return cleaned


# ─── Executores individuais ────────────────────────────────────────────────────

def _cmd_status(db: Session, tenant_id: int, lead: Lead, args: str) -> None:
    val = args.strip().lower()
    if val not in STATUS_VALID:
        return
    old = lead.status
    if old == val:
        return
    lead.status = val
    lead.updated_at = _utcnow()
    _log(db, tenant_id, lead.id, "status_changed", f"{old} → {val} (via Hermes)")


def _cmd_interest(db: Session, tenant_id: int, lead: Lead, args: str) -> None:
    val = args[:255].strip()
    if not val or lead.interest == val:
        return
    lead.interest = val
    lead.updated_at = _utcnow()
    _log(db, tenant_id, lead.id, "lead_updated", f"interesse atualizado: {val} (via Hermes)")


def _cmd_note(db: Session, tenant_id: int, lead: Lead, args: str) -> None:
    val = args[:1000].strip()
    if not val:
        return
    existing = lead.observacoes or ""
    timestamp = _utcnow().strftime("%d/%m %H:%M")
    lead.observacoes = f"{existing}\n[{timestamp}] {val}".strip()
    lead.updated_at = _utcnow()
    _log(db, tenant_id, lead.id, "note_added", val[:200])


def _cmd_followup(db: Session, tenant_id: int, lead: Lead, args: str) -> None:
    """
    Formatos aceitos:
      "Título do follow-up" 2025-05-10T14:00
      Título simples 2025-05-10T14:00
    """
    # Extrai datetime do final
    dt_match = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})", args)
    if not dt_match:
        return
    dt_str = dt_match.group(1)
    titulo = args[: dt_match.start()].strip().strip('"').strip("'").strip()
    if not titulo:
        titulo = "Follow-up agendado pelo Hermes"

    try:
        dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
    except ValueError:
        return

    fu = CrmFollowup(
        tenant_id=tenant_id,
        lead_id=lead.id,
        titulo=titulo,
        data_hora=dt,
        canal="whatsapp",
        status="pendente",
    )
    db.add(fu)
    _log(db, tenant_id, lead.id, "followup_created", f"{titulo} em {dt_str} (via Hermes)")


def _cmd_kanban(db: Session, tenant_id: int, lead: Lead, args: str) -> None:
    """Encontra coluna pelo nome (case-insensitive, match parcial) e move o lead."""
    name_query = args.strip().lower()
    if not name_query:
        return

    cols = db.query(CrmKanbanColumn).filter(CrmKanbanColumn.tenant_id == tenant_id).all()
    match = next(
        (c for c in cols if name_query in c.name.lower() or c.name.lower() in name_query),
        None,
    )
    if not match:
        return

    old_col = lead.kanban_column_id
    if old_col == match.id:
        return

    lead.kanban_column_id = match.id
    lead.updated_at = _utcnow()
    _log(db, tenant_id, lead.id, "kanban_moved", f"→ '{match.name}' (via Hermes)")
