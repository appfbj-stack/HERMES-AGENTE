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

    @staticmethod
    def _strip_data_envelope(data: dict | list | None) -> dict | list | None:
        if isinstance(data, dict):
            for key in ("data", "instance", "response"):
                nested = data.get(key)
                if isinstance(nested, (dict, list)):
                    return nested
        return data

    @staticmethod
    def _extract_value(data: dict | list | None, paths: list[tuple[str, ...]]) -> str | None:
        for path in paths:
            current = data
            for segment in path:
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(segment)
            if isinstance(current, str) and current.strip():
                return current.strip()
        return None

    async def _request_json(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        accepted_statuses: tuple[int, ...] = (200, 201),
    ) -> dict | list | None:
        response = await client.request(method, path, json=json, headers=self._headers())
        if response.status_code not in accepted_statuses:
            response.raise_for_status()
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise WhatsAppProviderError(f"Unexpected non-JSON response from Evolution endpoint {path}") from exc

    async def connect(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        payload = {"instanceName": connection.instance_name, "qrcode": True}
        if connection.webhook_url:
            payload["webhook"] = {"url": connection.webhook_url}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            data = await self._request_json(client, "POST", "/instance/create", json=payload)

        return self._normalize_status(data, default_status="connecting")

    async def get_status(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            data = await self._request_json(client, "GET", f"/instance/{connection.instance_name}/status", accepted_statuses=(200,))
        return self._normalize_status(data, default_status="unknown")

    async def get_qrcode(self, connection: CrmWhatsAppConnection) -> WhatsAppProviderStatus:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            data = None
            errors: list[str] = []
            for path in (
                f"/instance/{connection.instance_name}/qrcode",
                f"/instance/connect/{connection.instance_name}",
            ):
                try:
                    data = await self._request_json(client, "GET", path, accepted_statuses=(200, 201))
                    status = self._normalize_status(data, default_status="awaiting_qrcode")
                    if status.qr_code_base64 or status.status in {"connected", "open"}:
                        return status
                except (httpx.HTTPError, WhatsAppProviderError) as exc:
                    errors.append(f"{path}: {exc}")
            if data is not None:
                return self._normalize_status(data, default_status="awaiting_qrcode")
            raise WhatsAppProviderError("Could not fetch QR code from Evolution. Tried /qrcode and /connect endpoints. " + "; ".join(errors))

    async def disconnect(self, connection: CrmWhatsAppConnection) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as client:
            response = await client.delete(f"/instance/{connection.instance_name}", headers=self._headers())
            response.raise_for_status()

    async def send_text(self, connection: CrmWhatsAppConnection, number: str, text: str) -> dict | list | None:
        payload = {
            "instanceName": connection.instance_name,
            "number": number.split("@")[0],
            "text": text,
            "delay": 0,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            return await self._request_json(client, "POST", "/message/sendText", json=payload)

    def _normalize_status(self, data: dict | list, *, default_status: str) -> WhatsAppProviderStatus:
        data = self._strip_data_envelope(data)
        if isinstance(data, list):
            return WhatsAppProviderStatus(status=default_status, raw=data)

        qr_code = self._extract_value(
            data,
            [
                ("qrcode",),
                ("qr",),
                ("base64",),
                ("code",),
                ("qrcode", "base64"),
                ("qrcode", "code"),
                ("pairingCode",),
            ],
        )
        if qr_code and not qr_code.startswith("data:image"):
            qr_code = f"data:image/png;base64,{qr_code}"

        connected_phone = self._extract_value(
            data,
            [
                ("number",),
                ("phone",),
                ("ownerJid",),
                ("wid",),
                ("instance", "wid"),
                ("instance", "phone"),
            ],
        )

        status = (
            data.get("status")
            or data.get("state")
            or data.get("connectionStatus")
            or data.get("instanceStatus")
            or data.get("connection")
            or data.get("instance")
            or ("connected" if connected_phone else default_status)
        )
        if isinstance(status, dict):
            status = (
                status.get("state")
                or status.get("status")
                or status.get("connectionStatus")
                or default_status
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
