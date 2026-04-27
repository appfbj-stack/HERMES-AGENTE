from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.models import CrmWhatsAppConnection

settings = get_settings()


class WhatsAppProviderError(RuntimeError):
    pass


@dataclass
class WhatsAppProviderStatus:
    status: str
    connected_phone: str | None = None
    qr_code_base64: str | None = None
    raw: dict | list | None = None


class WhatsAppProvider:
    async def connect(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        raise NotImplementedError

    async def get_status(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        raise NotImplementedError

    async def get_qrcode(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        raise NotImplementedError

    async def disconnect(self, connection: CrmWhatsAppConnection) -> None:
        raise NotImplementedError

    async def send_text(self, connection: CrmWhatsAppConnection, number: str, text: str) -> dict | list | None:
        raise NotImplementedError


class EvolutionGoProvider(WhatsAppProvider):
    def __init__(self, connection: CrmWhatsAppConnection):
        self.connection = connection
        self.base_url = (connection.api_base_url or settings.evolution_api_base_url).rstrip("/")
        self.api_key = connection.api_key or settings.evolution_api_key
        self.api_key_header = settings.evolution_api_key_header or "apikey"

        if not self.base_url:
            raise WhatsAppProviderError("Evolution API base URL is not configured")
        if not self.api_key:
            raise WhatsAppProviderError("Evolution API key is not configured")

    def _headers(self) -> dict[str, str]:
        return {self.api_key_header: self.api_key, "Content-Type": "application/json"}

    async def connect(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        payload = {"instanceName": connection.instance_name, "qrcode": True}
        if connection.webhook_url:
            payload["webhook"] = {"url": connection.webhook_url}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.post("/instance/create", json=payload, headers=self._headers())
            response.raise_for_status()
            data = response.json()

        return self._normalize_status(data, default_status="connecting")

    async def get_status(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.get(f"/instance/{connection.instance_name}/status", headers=self._headers())
            response.raise_for_status()
            data = response.json()
        return self._normalize_status(data, default_status="unknown")

    async def get_qrcode(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.get(f"/instance/{connection.instance_name}/qrcode", headers=self._headers())
            response.raise_for_status()
            data = response.json()
        return self._normalize_status(data, default_status="awaiting_qrcode")

    async def disconnect(self, connection: CrmWhatsAppConnection) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.delete(f"/instance/{connection.instance_name}", headers=self._headers())
            response.raise_for_status()

    async def send_text(self, connection: CrmWhatsAppConnection, number: str, text: str) -> dict | list | None:
        payload = {
            "instanceName": connection.instance_name,
            "number": number,
            "text": text,
            "delay": 0,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.post("/message/sendText", json=payload, headers=self._headers())
            response.raise_for_status()
            return response.json() if response.content else None

    def _normalize_status(self, data: dict | list, *, default_status: str) -> WhatsAppProviderStatus:
        if isinstance(data, list):
            return WhatsAppProviderStatus(status=default_status, raw=data)

        qr_code = None
        for key in ("qrcode", "qr", "base64", "code"):
            value = data.get(key)
            if isinstance(value, str) and value:
                qr_code = value
                break

        connected_phone = None
        for key in ("number", "phone", "ownerJid", "wid"):
            value = data.get(key)
            if isinstance(value, str) and value:
                connected_phone = value
                break

        status = (
            data.get("status")
            or data.get("state")
            or data.get("connectionStatus")
            or ("connected" if connected_phone else default_status)
        )
        return WhatsAppProviderStatus(
            status=str(status),
            connected_phone=connected_phone,
            qr_code_base64=qr_code,
            raw=data,
        )


def get_provider(connection: CrmWhatsAppConnection) -> WhatsAppProvider:
    if connection.provider == "evolution_go":
        return EvolutionGoProvider(connection)
    raise WhatsAppProviderError(f"Unsupported WhatsApp provider: {connection.provider}")
