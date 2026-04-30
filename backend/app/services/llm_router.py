"""
Router inteligente para modelos de LLM baseado no tipo de usuário

Hermes Cliente:
- Primary: DeepSeek
- Fallback: GLM 4.7 Flash

Hermes Admin Master:
- Primary: GLM 4.7
- Fallback: GLM 4.7 Flash
- Last Fallback: DeepSeek
"""
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.models import User
from app.services.deepseek_service import call_deepseek
from app.services.openrouter_service import call_glm_47, call_glm_flash

logger = get_logger(__name__)


class LLMRoutingError(RuntimeError):
    """Erro padronizado quando nenhum provedor de IA consegue responder."""

    pass


async def route_llm(
    user: User,
    messages: list[dict[str, Any]],
    tenant_id: int | None = None,
) -> dict[str, Any]:
    """
    Roteia a requisião para o modelo apropriado baseado no tipo de usuário
    
    Args:
        user: Usuário atual
        messages: Lista de mensagens no formato {role, content}
        tenant_id: ID do tenant (para clientes comuns)
    
    Returns:
        Resposta do modelo de IA
    """
    start_time = datetime.now(timezone.utc)
    
    # Lógica de roteamento
    if user.is_super_admin:
        # Hermes Admin Master: GLM 4.7 → GLM 4.7 Flash → DeepSeek
        return await _route_admin_master(messages, start_time)
    else:
        # Hermes Cliente: DeepSeek → GLM 4.7 Flash
        return await _route_client(messages, tenant_id, start_time)


async def _route_admin_master(
    messages: list[dict[str, Any]],
    start_time: datetime
) -> dict[str, Any]:
    """Rota para Admin Master: GLM 4.7 → GLM 4.7 Flash → DeepSeek"""
    logger.info("[LLM Router] Usando Hermes Admin Master (super_admin)")
    
    try:
        # 1ª tentativa: GLM 4.7 (modelo mais inteligente)
        logger.info("[LLM Router] Tentando GLM 4.7...")
        return await call_glm_47(messages)
    except Exception as exc:
        logger.warning("[LLM Router] GLM 4.7 falhou: %s", exc)
        
        try:
            # 2ª tentativa: GLM 4.7 Flash (mais rápido)
            logger.info("[LLM Router] Tentando GLM 4.7 Flash como fallback...")
            return await call_glm_flash(messages)
        except Exception as exc:
            logger.warning("[LLM Router] GLM 4.7 Flash falhou: %s", exc)
            
            try:
                # 3ª tentativa: DeepSeek (último fallback)
                logger.info("[LLM Router] Tentando DeepSeek como último fallback...")
                return await call_deepseek(messages)
            except Exception as exc:
                logger.error("[LLM Router] Todos os modelos falharam no fluxo admin: %s", exc)
            raise LLMRoutingError("Todos os modelos de IA estão indisponíveis")


async def _route_client(
    messages: list[dict[str, Any]],
    tenant_id: int | None,
    start_time: datetime
) -> dict[str, Any]:
    """Rota para Cliente Comum: DeepSeek → GLM 4.7 Flash"""
    logger.info(f"[LLM Router] Usando Hermes Cliente (tenant_id={tenant_id})")
    
    try:
        # 1ª tentativa: DeepSeek (modelo oficial do cliente)
        logger.info("[LLM Router] Tentando DeepSeek...")
        return await call_deepseek(messages)
    except Exception as exc:
        logger.warning("[LLM Router] DeepSeek falhou: %s", exc)
        
        try:
            # 2ª tentativa: GLM 4.7 Flash (fallback)
            logger.info("[LLM Router] Tentando GLM 4.7 Flash como fallback...")
            return await call_glm_flash(messages)
        except Exception as exc:
            logger.error("[LLM Router] Todos os modelos falharam no fluxo cliente: %s", exc)
            raise LLMRoutingError("Todos os modelos de IA estão indisponíveis")


def format_messages_for_llm(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Formata mensagens para o formato correto da API
    
    Args:
        messages: Lista de mensagens
    
    Returns:
        Lista formatada para APIs de LLM
    """
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    return formatted


def parse_llm_response(response: dict[str, Any]) -> str:
    """
    Extrai o texto da resposta do modelo
    
    Args:
        response: Resposta do modelo de IA
    
    Returns:
        Texto da resposta
    """
    try:
        # Formato padrão OpenAI/DeepSeek
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        
        # Formato alternativo
        if "message" in response:
            return response["message"]["content"]
        
        # Formato direto
        if "content" in response:
            return response["content"]
        
        # Última tentativa: converter tudo para string
        return str(response)
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        logger.error("[LLM Router] Erro ao parsear resposta: %s", exc)
        return "Erro ao processar resposta do modelo"


def log_llm_usage(
    tenant_id: int | None,
    user_id: int | None,
    model: str,
    used_tokens: int,
    fallback_used: bool,
    success: bool,
    duration_ms: float,
    user_role: str,
    error_message: str | None = None,
) -> None:
    """
    Registra uso de LLM para análise e logs
    
    Args:
        tenant_id: ID do tenant
        user_id: ID do usuário
        model: Modelo usado
        used_tokens: Tokens utilizados
        fallback_used: Se usou fallback
        success: Se a requisição teve sucesso
        error_message: Mensagem de erro se houver
        duration_ms: Tempo em milissegundos
        user_role: Tipo de usuário (admin/client)
    """
    logger.info(
        f"[LLM Usage] "
        f"role={user_role} "
        f"tenant_id={tenant_id} "
        f"user_id={user_id} "
        f"model={model} "
        f"tokens={used_tokens} "
        f"fallback={fallback_used} "
        f"success={success} "
        f"duration_ms={duration_ms} ms"
    )
    
    if error_message:
        logger.error(f"[LLM Usage] Erro: {error_message}")
