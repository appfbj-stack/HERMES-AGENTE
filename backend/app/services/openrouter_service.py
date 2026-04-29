"""
Serviço de integração com OpenRouter (GLM 4.7, GLM 4.7 Flash)
"""
import os
from typing import Any

import httpx

from app.core.config import get_settings


async def call_glm_47(
    messages: list[dict[str, Any]],
    model: str = "z-ai/glm-4.7",
    temperature: float = 0.7,
    max_tokens: int = None,
) -> dict[str, Any]:
    """Chama GLM 4.7 via OpenRouter"""
    settings = get_settings()
    api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY não configurada")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            for msg in messages
        ],
        "temperature": temperature,
        "stream": False,
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hermes.fbautomacao.space"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Erro HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise Exception(f"Erro ao chamar GLM 4.7: {str(e)}")


async def call_glm_flash(
    messages: list[dict[str, Any]],
    model: str = "z-ai/glm-4.7-flash",
    temperature: float = 0.7,
    max_tokens: int = None,
) -> dict[str, Any]:
    """Chama GLM 4.7 Flash via OpenRouter (mais rápido e barato)"""
    settings = get_settings()
    api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY não configurada")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            for msg in messages
        ],
        "temperature": temperature,
        "stream": False,
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Erro HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise Exception(f"Erro ao chamar GLM 4.7 Flash: {str(e)}")


async def call_openrouter_with_fallback(
    messages: list[dict[str, Any]],
    model: str = "z-ai/glm-4.7",
    temperature: float = 0.7,
    max_tokens: int = None,
    fallback_model: str = None,
) -> dict[str, Any]:
    """Chama OpenRouter com fallback"""
    try:
        return await call_openrouter(model, messages, temperature, max_tokens)
    except Exception as e:
        print(f"[OpenRouter] Erro no modelo {model}, tentando fallback {fallback_model}: {str(e)}")
        if fallback_model:
            return await call_openrouter(fallback_model, messages, temperature, max_tokens)
        raise


async def call_openrouter(
    messages: list[dict[str, Any]],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = None,
) -> dict[str, Any]:
    """Chama qualquer modelo via OpenRouter"""
    settings = get_settings()
    api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY não configurada")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            for msg in messages
        ],
        "temperature": temperature,
        "stream": False,
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Erro HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise Exception(f"Erro ao chamar OpenRouter: {str(e)}")
