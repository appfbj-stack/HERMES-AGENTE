"""
Routes para a página de Agenda:
  GET  /agenda/reminders       — lembretes do tenant (pendentes/agendados)
  GET  /agenda/appointments    — compromissos do tenant (não-cancelados)
  PATCH /agenda/reminders/{id} — atualizar status de um lembrete
  PATCH /agenda/appointments/{id} — atualizar status de um compromisso
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import AgentAppointment, AgentReminder, User
from app.schemas import (
    AgentAppointmentOut,
    AgentAppointmentUpdate,
    AgentReminderOut,
    AgentReminderUpdate,
)

router = APIRouter(prefix="/agenda", tags=["agenda"])

VALID_REMINDER_STATUSES = {"pending", "scheduled", "sent", "cancelled", "done"}
VALID_APPOINTMENT_STATUSES = {"scheduled", "confirmed", "cancelled", "done"}


# ── Reminders ──────────────────────────────────────────────────────────────���──


@router.get("/reminders", response_model=list[AgentReminderOut])
def list_reminders(
    include_done: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AgentReminder).filter(AgentReminder.tenant_id == current_user.tenant_id)
    if not include_done:
        q = q.filter(AgentReminder.status.in_(["pending", "scheduled"]))
    return (
        q.order_by(AgentReminder.remind_at.asc())
        .limit(limit)
        .all()
    )


@router.patch("/reminders/{reminder_id}", response_model=AgentReminderOut)
def update_reminder(
    reminder_id: int,
    payload: AgentReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = (
        db.query(AgentReminder)
        .filter(
            AgentReminder.id == reminder_id,
            AgentReminder.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado")
    if payload.status is not None:
        if payload.status not in VALID_REMINDER_STATUSES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Status inválido: {payload.status}")
        reminder.status = payload.status
        if payload.status in ("sent", "done"):
            reminder.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


# ── Appointments ──────────────────────────────────────────────────────────────


@router.get("/appointments", response_model=list[AgentAppointmentOut])
def list_appointments(
    include_cancelled: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AgentAppointment).filter(AgentAppointment.tenant_id == current_user.tenant_id)
    if not include_cancelled:
        q = q.filter(AgentAppointment.status != "cancelled")
    return (
        q.order_by(AgentAppointment.scheduled_at.asc())
        .limit(limit)
        .all()
    )


@router.patch("/appointments/{appointment_id}", response_model=AgentAppointmentOut)
def update_appointment(
    appointment_id: int,
    payload: AgentAppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = (
        db.query(AgentAppointment)
        .filter(
            AgentAppointment.id == appointment_id,
            AgentAppointment.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compromisso não encontrado")
    if payload.status is not None:
        if payload.status not in VALID_APPOINTMENT_STATUSES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Status inválido: {payload.status}")
        appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment
