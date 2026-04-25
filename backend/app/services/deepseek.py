"""
Cliente LLM compatível com OpenAI Chat Completions.
Funciona com OpenRouter, DeepSeek direto ou qualquer outro endpoint compatível.
Configurado via env: LLM_API_KEY, LLM_API_URL, LLM_MODEL.
"""
import httpx
from ..config import settings


def _build_headers() -> dict:
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    # Headers opcionais recomendados pela OpenRouter
    if "openrouter.ai" in settings.llm_api_url:
        if settings.openrouter_referer:
            headers["HTTP-Referer"] = settings.openrouter_referer
        if settings.openrouter_title:
            headers["X-Title"] = settings.openrouter_title
    return headers


async def chat_completion(messages: list[dict], model: str | None = None) -> dict:
    """
    Retorna: {"content": str, "tokens_in": int, "tokens_out": int, "model": str}
    """
    if not settings.llm_api_key:
        return {
            "content": "[LLM desativado: configure LLM_API_KEY no .env]",
            "tokens_in": 0,
            "tokens_out": 0,
            "model": settings.llm_model,
        }

    payload = {
        "model": model or settings.llm_model,
        "messages": messages,
        "temperature": 0.7,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(settings.llm_api_url, json=payload, headers=_build_headers())
        if r.status_code >= 400:
            # Mensagem mais útil para debug
            return {
                "content": f"[Erro LLM {r.status_code}: {r.text[:300]}]",
                "tokens_in": 0,
                "tokens_out": 0,
                "model": payload["model"],
            }
        data = r.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {}) or {}
    return {
        "content": content,
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "model": data.get("model", payload["model"]),
    }
