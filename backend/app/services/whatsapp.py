import httpx
from ..config import settings


async def send_whatsapp_message(to: str, text: str) -> dict | None:
    """
    Stub preparado para WhatsApp Cloud API / Z-API / Evolution.
    Configure WHATSAPP_API_URL e WHATSAPP_API_TOKEN no .env.
    """
    if not settings.whatsapp_api_url or not settings.whatsapp_api_token:
        return None

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(settings.whatsapp_api_url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
