from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


async def call_hermes(messages: list[dict[str, str]]) -> tuple[str, int]:
    headers = {}
    if settings.hermes_agent_api_key:
        headers["Authorization"] = f"Bearer {settings.hermes_agent_api_key}"

    payload = {"messages": messages}
    async with httpx.AsyncClient(base_url=settings.hermes_agent_url, timeout=45.0) as client:
        response = await client.post(settings.hermes_agent_path, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, dict):
        if data.get("response"):
            return str(data["response"]), int(data.get("tokens_used", 0))
        if data.get("content"):
            return str(data["content"]), int(data.get("tokens_used", 0))
        if data.get("answer"):
            return str(data["answer"]), int(data.get("tokens_used", 0))
        choices = data.get("choices")
        if choices:
            return str(choices[0]["message"]["content"]), int(data.get("usage", {}).get("total_tokens", 0))

    raise ValueError("Unsupported Hermes response format")


async def generate_reply(messages: list[dict[str, str]]) -> tuple[str, int]:
    if settings.ai_provider == "hermes":
        try:
            return await call_hermes(messages)
        except Exception:
            if not settings.deepseek_api_key:
                fallback = "O agente Hermes está indisponível no momento. Tente novamente em instantes."
                return fallback, 0

    if not settings.deepseek_api_key:
        fallback = "Configuração da DeepSeek ausente. Resposta automática indisponível no momento."
        return fallback, 0

    payload: dict[str, Any] = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {settings.deepseek_api_key}"}

    async with httpx.AsyncClient(base_url=settings.deepseek_base_url, timeout=30.0) as client:
        response = await client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    usage = int(data.get("usage", {}).get("total_tokens", 0))
    return content, usage
