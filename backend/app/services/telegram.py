import httpx

from app.core.config import get_settings

settings = get_settings()


async def send_telegram_message(chat_external_id: str, text: str) -> None:
    if not settings.telegram_bot_token:
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_external_id, "text": text}
    async with httpx.AsyncClient(timeout=20.0) as client:
        await client.post(url, json=payload)

