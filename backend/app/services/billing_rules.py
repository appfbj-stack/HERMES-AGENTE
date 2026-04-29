from sqlalchemy.orm import Session

from app.models import Credit, Tenant, TenantModule
from app.core.logging import get_logger

logger = get_logger(__name__)


def check_plan_limits(db: Session, tenant_id: int) -> dict:
    """
    Verifica limites do plano de um tenant.

    Retorna:
    {
        "active": bool,          # Tenant está ativo
        "has_credits": bool,     # Tem créditos disponíveis
        "credits_remaining": int,  # Créditos restantes
        "is_blocked": bool,       # Está bloqueado (plano vencido ou sem créditos)
        "block_reason": str | None  # Motivo do bloqueio
    }
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return {
            "active": False,
            "has_credits": False,
            "credits_remaining": 0,
            "is_blocked": True,
            "block_reason": "Tenant não encontrado",
        }

    if not tenant.active:
        return {
            "active": False,
            "has_credits": False,
            "credits_remaining": 0,
            "is_blocked": True,
            "block_reason": "Tenant inativo",
        }

    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        return {
            "active": True,
            "has_credits": False,
            "credits_remaining": 0,
            "is_blocked": True,
            "block_reason": "Sem créditos configurados",
        }

    credits_remaining = credit.remaining
    has_credits = credits_remaining > 0

    block_reason = None
    is_blocked = False

    if credits_remaining <= 0:
        is_blocked = True
        block_reason = "Limite de mensagens atingido"

    return {
        "active": True,
        "has_credits": has_credits,
        "credits_remaining": credits_remaining,
        "is_blocked": is_blocked,
        "block_reason": block_reason,
    }


def can_use_ai(db: Session, tenant_id: int) -> tuple[bool, str | None]:
    """
    Verifica se o tenant pode usar IA.

    Retorna:
    (can_use, reason)
    - can_use: True se pode usar IA
    - reason: Motivo se não pode usar, None se pode
    """
    # Verificar se módulo CRM está ativo
    module = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).first()
    if not module or not module.crm:
        return False, "Módulo CRM não ativo"

    # Verificar limites do plano
    plan_status = check_plan_limits(db, tenant_id)

    if plan_status["is_blocked"]:
        return False, plan_status["block_reason"]

    return True, None


def count_message(db: Session, tenant_id: int) -> bool:
    """
    Contabiliza uma mensagem usada pelo tenant.

    Retorna:
    - True: mensagem contabilizada com sucesso
    - False: erro ao contabilizar (sem créditos, etc.)
    """
    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        logger.error(f"Credit not found for tenant {tenant_id}")
        return False

    if credit.remaining <= 0:
        logger.warning(f"Tenant {tenant_id} has no credits remaining")
        return False

    credit.used += 1
    credit.remaining -= 1

    db.commit()

    logger.info(f"Message counted for tenant {tenant_id}. Remaining: {credit.remaining}/{credit.total}")
    return True


def get_tenant_credits(db: Session, tenant_id: int) -> dict:
    """
    Retorna informações de créditos do tenant.
    """
    credit = db.query(Credit).filter(Credit.tenant_id == tenant_id).first()
    if not credit:
        return {
            "total": 0,
            "used": 0,
            "remaining": 0,
        }

    return {
        "total": credit.total,
        "used": credit.used,
        "remaining": credit.remaining,
    }
