"""
Endpoints de cobrança via Asaas.
- Cliente vê seu plano/status
- Cliente assina um plano
- Cliente compra pacote avulso de créditos
- Webhook do Asaas atualiza status de pagamento
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.deps import get_current_user
from app.models import Credit, Payment, Plan, Subscription, Tenant, User
from app.schemas import (
    BuyCreditsRequest,
    CreateSubscriptionRequest,
    PaymentOut,
    PlanOut,
    SubscriptionOut,
)
from app.services import asaas

router = APIRouter(tags=["billing"])


# ============================================================
# Catálogo de planos (público)
# ============================================================
@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.active == True).order_by(Plan.price_cents).all()


# ============================================================
# Assinatura do tenant logado
# ============================================================
@router.get("/billing/subscription", response_model=SubscriptionOut | None)
def my_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.tenant_id == user.tenant_id).first()
    if not sub:
        return None
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    out = SubscriptionOut.model_validate(sub)
    if plan:
        out.plan = PlanOut.model_validate(plan)
    return out


@router.post("/billing/subscribe", response_model=PaymentOut)
async def subscribe_to_plan(
    payload: CreateSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.asaas_api_key:
        raise HTTPException(status_code=503, detail="Cobrança não configurada (ASAAS_API_KEY ausente)")

    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.active == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

    # 1. Cria/encontra customer no Asaas
    customer = await asaas.get_or_create_customer(
        name=tenant.name, email=tenant.email, cpf_cnpj=payload.cpf_cnpj
    )

    # 2. Cria assinatura recorrente
    asaas_sub = await asaas.create_subscription(
        customer_id=customer["id"],
        value_cents=plan.price_cents,
        billing_type=payload.billing_type,
        description=f"Assinatura {plan.name} — Meu Assistente Pessoal",
    )

    # 3. Salva no banco
    sub = db.query(Subscription).filter(Subscription.tenant_id == user.tenant_id).first()
    if not sub:
        sub = Subscription(
            tenant_id=user.tenant_id,
            plan_id=plan.id,
            status="pending",
            asaas_customer_id=customer["id"],
            asaas_subscription_id=asaas_sub["id"],
        )
        db.add(sub)
    else:
        sub.plan_id = plan.id
        sub.status = "pending"
        sub.asaas_customer_id = customer["id"]
        sub.asaas_subscription_id = asaas_sub["id"]

    # 4. Cria registro de Payment com a primeira cobrança
    pay = Payment(
        tenant_id=user.tenant_id,
        type="subscription",
        value_cents=plan.price_cents,
        status="pending",
        billing_type=payload.billing_type,
        credits_added=plan.monthly_credits,
    )
    # Asaas retorna primeira cobrança no campo "id" da subscription? Não — gera quando vence.
    # Mas pra UX, criamos um Payment com link da subscription.
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return pay


# ============================================================
# Compra avulsa de créditos
# ============================================================
@router.post("/billing/buy-credits", response_model=PaymentOut)
async def buy_credits(
    payload: BuyCreditsRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.asaas_api_key:
        raise HTTPException(status_code=503, detail="Cobrança não configurada (ASAAS_API_KEY ausente)")

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

    # 1. Cria/encontra customer
    customer = await asaas.get_or_create_customer(
        name=tenant.name, email=tenant.email, cpf_cnpj=payload.cpf_cnpj
    )

    # 2. Cria cobrança avulsa
    asaas_pay = await asaas.create_payment(
        customer_id=customer["id"],
        value_cents=payload.value_cents,
        billing_type=payload.billing_type,
        description=f"+{payload.credits} mensagens — Meu Assistente Pessoal",
    )

    # 3. Pega QR Code se for PIX
    pix_qr = None
    pix_payload = None
    if payload.billing_type == "PIX":
        try:
            pix_data = await asaas.get_pix_qr_code(asaas_pay["id"])
            pix_qr = pix_data.get("encodedImage")
            pix_payload = pix_data.get("payload")
        except Exception:  # noqa: BLE001
            pass

    # 4. Salva registro
    pay = Payment(
        tenant_id=user.tenant_id,
        asaas_payment_id=asaas_pay["id"],
        type="credits_pack",
        value_cents=payload.value_cents,
        status="pending",
        billing_type=payload.billing_type,
        invoice_url=asaas_pay.get("invoiceUrl"),
        pix_qr_code=pix_qr,
        pix_payload=pix_payload,
        credits_added=payload.credits,
    )
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return pay


@router.get("/billing/payments", response_model=list[PaymentOut])
def list_my_payments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Payment)
        .filter(Payment.tenant_id == user.tenant_id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )


# ============================================================
# Webhook do Asaas (eventos de pagamento)
# ============================================================
@router.post("/webhook/asaas")
async def asaas_webhook(
    request: Request,
    asaas_access_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Configurar no painel Asaas:
      Configurações > Integrações > Webhooks
      URL: https://api.meuchat.fbautomacao.space/webhook/asaas
      Token de autenticação: o mesmo de ASAAS_WEBHOOK_TOKEN
    """
    settings = get_settings()
    if settings.asaas_webhook_token and asaas_access_token != settings.asaas_webhook_token:
        raise HTTPException(status_code=401, detail="Token inválido")

    body = await request.json()
    event = body.get("event")
    payment_data = body.get("payment") or {}
    asaas_payment_id = payment_data.get("id")
    if not asaas_payment_id:
        return {"status": "ignored"}

    pay = db.query(Payment).filter(Payment.asaas_payment_id == asaas_payment_id).first()

    # Eventos relevantes
    if event in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
        if pay and pay.status not in ("confirmed", "received"):
            pay.status = "received"
            pay.paid_at = datetime.now(timezone.utc)
            # Credita as mensagens compradas
            credit = db.query(Credit).filter(Credit.tenant_id == pay.tenant_id).first()
            if credit and pay.credits_added > 0:
                credit.total += pay.credits_added
                credit.remaining += pay.credits_added
            # Reativa tenant se estava bloqueado
            tenant = db.query(Tenant).filter(Tenant.id == pay.tenant_id).first()
            if tenant and not tenant.active:
                tenant.active = True
            # Atualiza assinatura se for de plano
            if pay.type == "subscription":
                sub = db.query(Subscription).filter(Subscription.tenant_id == pay.tenant_id).first()
                if sub:
                    sub.status = "active"
                    sub.last_paid_at = datetime.now(timezone.utc)

    elif event == "PAYMENT_OVERDUE":
        if pay:
            pay.status = "overdue"
        # Marca assinatura inadimplente
        sub_id = payment_data.get("subscription")
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
            if sub:
                sub.status = "overdue"

    elif event in ("PAYMENT_REFUNDED", "PAYMENT_DELETED"):
        if pay:
            pay.status = "refunded" if event == "PAYMENT_REFUNDED" else "canceled"

    elif event == "SUBSCRIPTION_CANCELED":
        sub_id = body.get("subscription", {}).get("id")
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.asaas_subscription_id == sub_id).first()
            if sub:
                sub.status = "canceled"
                sub.canceled_at = datetime.now(timezone.utc)

    db.commit()
    return {"status": "ok", "event": event}
