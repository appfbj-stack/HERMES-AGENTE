"""
Cliente para a API do Asaas.
Documentação: https://docs.asaas.com/
"""
from datetime import date, timedelta
from typing import Any

import httpx

from app.core.config import get_settings


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "User-Agent": "MeuAssistentePessoal/1.0",
        "access_token": get_settings().asaas_api_key,
    }


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=get_settings().asaas_api_url,
        headers=_headers(),
        timeout=30.0,
    )


# ============================================================
# Customers
# ============================================================
async def create_customer(
    name: str,
    email: str,
    cpf_cnpj: str | None = None,
    phone: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "email": email,
    }
    if cpf_cnpj:
        payload["cpfCnpj"] = cpf_cnpj
    if phone:
        payload["phone"] = phone

    async with _client() as c:
        r = await c.post("/customers", json=payload)
        r.raise_for_status()
        return r.json()


async def find_customer_by_email(email: str) -> dict | None:
    async with _client() as c:
        r = await c.get("/customers", params={"email": email})
        r.raise_for_status()
        data = r.json()
    items = data.get("data") or []
    return items[0] if items else None


async def get_or_create_customer(name: str, email: str, cpf_cnpj: str | None = None) -> dict:
    existing = await find_customer_by_email(email)
    if existing:
        return existing
    return await create_customer(name, email, cpf_cnpj)


# ============================================================
# Subscriptions (cobrança recorrente mensal)
# ============================================================
async def create_subscription(
    customer_id: str,
    value_cents: int,
    billing_type: str = "PIX",  # PIX | BOLETO | CREDIT_CARD | UNDEFINED
    description: str = "Assinatura mensal",
    next_due_date: date | None = None,
) -> dict:
    if next_due_date is None:
        next_due_date = date.today() + timedelta(days=3)

    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": round(value_cents / 100, 2),
        "nextDueDate": next_due_date.isoformat(),
        "cycle": "MONTHLY",
        "description": description,
    }
    async with _client() as c:
        r = await c.post("/subscriptions", json=payload)
        r.raise_for_status()
        return r.json()


async def cancel_subscription(asaas_subscription_id: str) -> dict:
    async with _client() as c:
        r = await c.delete(f"/subscriptions/{asaas_subscription_id}")
        r.raise_for_status()
        return r.json()


# ============================================================
# Payments (cobrança avulsa - ex: pacote de créditos)
# ============================================================
async def create_payment(
    customer_id: str,
    value_cents: int,
    billing_type: str = "PIX",
    description: str = "Pacote de mensagens",
    due_date: date | None = None,
) -> dict:
    if due_date is None:
        due_date = date.today() + timedelta(days=3)

    payload = {
        "customer": customer_id,
        "billingType": billing_type,
        "value": round(value_cents / 100, 2),
        "dueDate": due_date.isoformat(),
        "description": description,
    }
    async with _client() as c:
        r = await c.post("/payments", json=payload)
        r.raise_for_status()
        return r.json()


async def get_pix_qr_code(payment_id: str) -> dict:
    """Retorna o QR Code PIX e o código copia-e-cola."""
    async with _client() as c:
        r = await c.get(f"/payments/{payment_id}/pixQrCode")
        r.raise_for_status()
        return r.json()


async def get_payment(payment_id: str) -> dict:
    async with _client() as c:
        r = await c.get(f"/payments/{payment_id}")
        r.raise_for_status()
        return r.json()
