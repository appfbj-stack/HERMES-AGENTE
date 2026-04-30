"""
Serviço de integração com LLMs (DeepSeek, GLM 4.7)
Roteamento inteligente baseado em tipo de usuário
"""
from typing import Any

from app.core.logging import get_logger
from app.core.config import get_settings
from app.services.llm_router import LLMRoutingError, parse_llm_response, route_llm

settings = get_settings()
logger = get_logger(__name__)


async def call_hermes(messages: list[dict[str, str]]) -> tuple[str, int]:
    """Chama Hermes Agent usando o roteador LLM"""
    from app.models import User

    user = User(is_super_admin=False, tenant_id=1, name="system", email="system@hermes.com", role="system", password="")
    response = await route_llm(user, messages, tenant_id=1)
    content = parse_llm_response(response)
    tokens = response.get("usage", {}).get("total_tokens", 0)
    return content, tokens


async def generate_reply(messages: list[dict[str, str]], tenant_id: int | None = None) -> tuple[str, int]:
    """Gera resposta usando o LLM Router"""
    from app.models import User

    resolved_tenant_id = tenant_id or 1
    user = User(
        is_super_admin=False,
        tenant_id=resolved_tenant_id,
        name="system",
        email="system@hermes.com",
        role="system",
        password="",
    )
    try:
        response = await route_llm(user, messages, tenant_id=resolved_tenant_id)
        content = parse_llm_response(response)
        tokens = response.get("usage", {}).get("total_tokens", 0)
        return content, tokens
    except LLMRoutingError as exc:
        logger.warning(
            "Todos os modelos de IA ficaram indisponíveis para tenant_id=%s: %s",
            resolved_tenant_id,
            exc,
        )
        raise ValueError("Todos os modelos de IA estão indisponíveis") from exc
