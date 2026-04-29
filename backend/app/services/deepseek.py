"""
Serviço de integração com LLMs (DeepSeek, GLM 4.7)
Roteamento inteligente baseado em tipo de usuário
"""
from typing import Any

from app.core.config import get_settings
from app.services.llm_router import route_llm, parse_llm_response

settings = get_settings()


async def call_hermes(messages: list[dict[str, str]]) -> tuple[str, int]:
    """Chama Hermes Agent usando o roteador LLM"""
    from app.models import User

    user = User(is_super_admin=False, tenant_id=1, name="system", email="system@hermes.com", role="system", password="")
    try:
        response = await route_llm(user, messages, tenant_id=1)
        content = parse_llm_response(response)
        tokens = response.get("usage", {}).get("total_tokens", 0)
        return content, tokens
    except Exception:
        raise


async def generate_reply(messages: list[dict[str, str]]) -> tuple[str, int]:
    """Gera resposta usando o LLM Router"""
    from app.models import User

    user = User(is_super_admin=False, tenant_id=1, name="system", email="system@hermes.com", role="system", password="")
    try:
        response = await route_llm(user, messages, tenant_id=1)
        content = parse_llm_response(response)
        tokens = response.get("usage", {}).get("total_tokens", 0)
        return content, tokens
    except Exception:
        raise ValueError("Todos os modelos de IA estão indisponíveis")
