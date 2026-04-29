"""
Serviço de integração com DeepSeek API
"""
import os
from typing import Any

import httpx

from app.core.config import get_settings


async def call_deepseek(
    messages: list[dict[str, Any]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
) -> dict[str, Any]:
    """Chama a API do DeepSeek"""
    settings = get_settings()
    api_key = settings.deepseek_api_key
    
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY não configurada")
    
    model = model or settings.deepseek_model
    
    # Payload DeepSeek (formato chat)
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
        "Content-Type": "application/json"
    }
    
    base_url = settings.deepseek_base_url or "https://api.deepseek.com"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise Exception(f"Erro HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise Exception(f"Erro ao chamar DeepSeek: {str(e)}")


async def call_deepseek_with_fallback(
    messages: list[dict[str, Any]],
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
    fallback_model: str = None,
) -> dict[str, Any]:
    """Chama DeepSeek com fallback para outro modelo"""
    try:
        return await call_deepseek(messages, model, temperature, max_tokens)
    except Exception as e:
        print(f"[DeepSeek] Erro, tentando fallback para {fallback_model}: {str(e)}")
        if fallback_model:
            return await call_deepseek(messages, fallback_model, temperature, max_tokens)
        raise
