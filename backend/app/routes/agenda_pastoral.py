"""
MÃ³dulo Agenda Pastoral â rotas multi-tenant
Prefixo: /agenda-pastoral
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user, require_module_enabled
from app.models import (
    PastoralAconselhamento,
    PastoralCulto,
    PastoralEvento,
    PastoralMembro,
    PastoralVisita,
    User,
)

router = APIRouter(
    prefix="/agenda-pastoral",
    tags=["agenda-pastoral"],
    dependencies=[Depends(require_module_enabled("agenda_pastoral", "Agenda Pastoral"))],
)


def utcnow():
    return datetime.now(timezone.utc)


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ââ Membro ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class MembroCreate(BaseModel):
    nome: str
    telefone: str | None = None
    email: str | None = None
    data_nascimento: date | None = None
    endereco: str | None = None
    data_batismo: date | None = None
    cargo: str | None = None
    ativo: bool = True
    observacoes: str | None = None

class MembroUpdate(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    email: str | None = None
    data_nascimento: date | None = None
    endereco: str | None = None
    data_batismo: date | None = None
    cargo: str | None = None
    ativo: bool | None = None
    observacoes: str | None = None

class MembroOut(ORM):
    id: int
    tenant_id: int
    nome: str
    telefone: str | None
    email: str | None
    data_nascimento: date | None
    endereco: str | None
    data_batismo: date | None
    cargo: str | None
    ativo: bool
    observacoes: str | None
    created_at: datetime
    updated_at: datetime


# ââ Culto âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class CultoCreate(BaseModel):
    tipo: str
    data_culto: datetime
    pregador: str | None = None
    tema: str | None = None
    presentes: int | None = None
    visitantes: int | None = None
    oferta: float | None = None
    observacoes: str | None = None

class CultoUpdate(BaseModel):
    tipo: str | None = None
    data_culto: datetime | None = None
    pregador: str | None = None
    tema: str | None = None
    presentes: int | None = None
    visitantes: int | None = None
    oferta: float | None = None
    observacoes: str | None = None

class CultoOut(ORM):
    id: int
    tenant_id: int
    tipo: str
    data_culto: datetime
    pregador: str | None
    tema: str | None
    presentes: int | None
    visitantes: int | None
    oferta: float | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime


# ââ Evento ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class EventoCreate(BaseModel):
    titulo: str
    data_inicio: datetime
    data_fim: datetime | None = None
    local: str | None = None
    descricao: str | None = None
    responsavel: str | None = None
    status: str = "planejado"

class EventoUpdate(BaseModel):
    titulo: str | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    local: str | None = None
    descricao: str | None = None
    responsavel: str | None = None
    status: str | None = None

class EventoOut(ORM):
    id: int
    tenant_id: int
    titulo: str
    data_inicio: datetime
    data_fim: datetime | None
    local: str | None
    descricao: str | None
    responsavel: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# ââ Visita ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class VisitaCreate(BaseModel):
    membro_id: int | None = None
    nome_visitado: str | None = None
    data_visita: datetime
    local: str | None = None
    motivo: str | None = None
    feito_por: str | None = None
    observacoes: str | None = None

class VisitaUpdate(BaseModel):
    membro_id: int | None = None
    nome_visitado: str | None = None
    data_visita: datetime | None = None
    local: str | None = None
    motivo: str | None = None
    feito_por: str | None = None
    observacoes: str | None = None

class VisitaOut(ORM):
    id: int
    tenant_id: int
    membro_id: int | None
    nome_visitado: str | None
    data_visita: datetime
    local: str | None
    motivo: str | None
    feito_por: str | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime


# ââ Aconselhamento ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class AconselhamentoCreate(BaseModel):
    membro_id: int | None = None
    nome_aconselhado: str | None = None
    data_sessao: datetime
    assunto: str | None = None
    confidencial: bool = True
    feito_por: str | None = None
    observacoes: str | None = None

class AconselhamentoUpdate(BaseModel):
    membro_id: int | None = None
    nome_aconselhado: str | None = None
    data_sessao: datetime | None = None
    assunto: str | None = None
    confidencial: bool | None = None
    feito_por: str | None = None
    observacoes: str | None = None

class AconselhamentoOut(ORM):
    id: int
    tenant_id: int
    membro_id: int | None
    nome_aconselhado: str | None
    data_sessao: datetime
    assunto: str | None
    confidencial: bool
    feito_por: str | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Dashboard
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/dashboard")
def pastoral_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = current_user.tenant_id
    total_membros = db.query(PastoralMembro).filter(PastoralMembro.tenant_id == tid).count()
    membros_ativos = db.query(PastoralMembro).filter(
        PastoralMembro.tenant_id == tid, PastoralMembro.ativo.is_(True)
    ).count()
    total_cultos = db.query(PastoralCulto).filter(PastoralCulto.tenant_id == tid).count()
    total_eventos = db.query(PastoralEvento).filter(PastoralEvento.tenant_id == tid).count()
    total_visitas = db.query(PastoralVisita).filter(PastoralVisita.tenant_id == tid).count()
    total_aconselhamentos = db.query(PastoralAconselhamento).filter(
        PastoralAconselhamento.tenant_id == tid
    ).count()

    ultimo_culto = (
        db.query(PastoralCulto)
        .filter(PastoralCulto.tenant_id == tid)
        .order_by(PastoralCulto.data_culto.desc())
        .first()
    )
    proximo_evento = (
        db.query(PastoralEvento)
        .filter(
            PastoralEvento.tenant_id == tid,
            PastoralEvento.data_inicio >= utcnow(),
            PastoralEvento.status.in_(["planejado", "confirmado"]),
        )
        .order_by(PastoralEvento.data_inicio.asc())
        .first()
    )

    return {
        "total_membros": total_membros,
        "membros_ativos": membros_ativos,
        "total_cultos": total_cultos,
        "total_eventos": total_eventos,
        "total_visitas": total_visitas,
        "total_aconselhamentos": total_aconselhamentos,
        "ultimo_culto": CultoOut.model_validate(ultimo_culto) if ultimo_culto else None,
        "proximo_evento": EventoOut.model_validate(proximo_evento) if proximo_evento else None,
    }


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Membros CRUD
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/membros", response_model=list[MembroOut])
def list_membros(
    ativo: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PastoralMembro).filter(PastoralMembro.tenant_id == current_user.tenant_id)
    if ativo is not None:
        q = q.filter(PastoralMembro.ativo.is_(ativo))
    if search:
        q = q.filter(PastoralMembro.nome.ilike(f"%{search}%"))
    return q.order_by(PastoralMembro.nome.asc()).offset(offset).limit(limit).all()


@router.post("/membros", response_model=MembroOut, status_code=status.HTTP_201_CREATED)
def create_membro(
    payload: MembroCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membro = PastoralMembro(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return membro


@router.get("/membros/{membro_id}", response_model=MembroOut)
def get_membro(
    membro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membro = db.query(PastoralMembro).filter(
        PastoralMembro.id == membro_id, PastoralMembro.tenant_id == current_user.tenant_id
    ).first()
    if not membro:
        raise HTTPException(status_code=404, detail="Membro nÃ£o encontrado")
    return membro


@router.patch("/membros/{membro_id}", response_model=MembroOut)
def update_membro(
    membro_id: int,
    payload: MembroUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membro = db.query(PastoralMembro).filter(
        PastoralMembro.id == membro_id, PastoralMembro.tenant_id == current_user.tenant_id
    ).first()
    if not membro:
        raise HTTPException(status_code=404, detail="Membro nÃ£o encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(membro, k, v)
    db.commit()
    db.refresh(membro)
    return membro


@router.delete("/membros/{membro_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membro(
    membro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membro = db.query(PastoralMembro).filter(
        PastoralMembro.id == membro_id, PastoralMembro.tenant_id == current_user.tenant_id
    ).first()
    if not membro:
        raise HTTPException(status_code=404, detail="Membro nÃ£o encontrado")
    db.delete(membro)
    db.commit()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Cultos CRUD
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/cultos", response_model=list[CultoOut])
def list_cultos(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(PastoralCulto)
        .filter(PastoralCulto.tenant_id == current_user.tenant_id)
        .order_by(PastoralCulto.data_culto.desc())
        .offset(offset).limit(limit).all()
    )


@router.post("/cultos", response_model=CultoOut, status_code=status.HTTP_201_CREATED)
def create_culto(payload: CultoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    culto = PastoralCulto(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(culto); db.commit(); db.refresh(culto)
    return culto


@router.get("/cultos/{culto_id}", response_model=CultoOut)
def get_culto(culto_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    culto = db.query(PastoralCulto).filter(PastoralCulto.id == culto_id, PastoralCulto.tenant_id == current_user.tenant_id).first()
    if not culto:
        raise HTTPException(status_code=404, detail="Culto nÃ£o encontrado")
    return culto


@router.patch("/cultos/{culto_id}", response_model=CultoOut)
def update_culto(culto_id: int, payload: CultoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    culto = db.query(PastoralCulto).filter(PastoralCulto.id == culto_id, PastoralCulto.tenant_id == current_user.tenant_id).first()
    if not culto:
        raise HTTPException(status_code=404, detail="Culto nÃ£o encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(culto, k, v)
    db.commit(); db.refresh(culto)
    return culto


@router.delete("/cultos/{culto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_culto(culto_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    culto = db.query(PastoralCulto).filter(PastoralCulto.id == culto_id, PastoralCulto.tenant_id == current_user.tenant_id).first()
    if not culto:
        raise HTTPException(status_code=404, detail="Culto nÃ£o encontrado")
    db.delete(culto); db.commit()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Eventos CRUD
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/eventos", response_model=list[EventoOut])
def list_eventos(
    status_filter: str | None = Query(default=None, alias="status"),
    proximos: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PastoralEvento).filter(PastoralEvento.tenant_id == current_user.tenant_id)
    if status_filter:
        q = q.filter(PastoralEvento.status == status_filter)
    if proximos:
        q = q.filter(PastoralEvento.data_inicio >= utcnow())
    return q.order_by(PastoralEvento.data_inicio.asc()).offset(offset).limit(limit).all()


@router.post("/eventos", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def create_evento(payload: EventoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evento = PastoralEvento(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(evento); db.commit(); db.refresh(evento)
    return evento


@router.get("/eventos/{evento_id}", response_model=EventoOut)
def get_evento(evento_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evento = db.query(PastoralEvento).filter(PastoralEvento.id == evento_id, PastoralEvento.tenant_id == current_user.tenant_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento nÃ£o encontrado")
    return evento


@router.patch("/eventos/{evento_id}", response_model=EventoOut)
def update_evento(evento_id: int, payload: EventoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evento = db.query(PastoralEvento).filter(PastoralEvento.id == evento_id, PastoralEvento.tenant_id == current_user.tenant_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento nÃ£o encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(evento, k, v)
    db.commit(); db.refresh(evento)
    return evento


@router.delete("/eventos/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evento(evento_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evento = db.query(PastoralEvento).filter(PastoralEvento.id == evento_id, PastoralEvento.tenant_id == current_user.tenant_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento nÃ£o encontrado")
    db.delete(evento); db.commit()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Visitas CRUD
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/visitas", response_model=list[VisitaOut])
def list_visitas(
    membro_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PastoralVisita).filter(PastoralVisita.tenant_id == current_user.tenant_id)
    if membro_id is not None:
        q = q.filter(PastoralVisita.membro_id == membro_id)
    return q.order_by(PastoralVisita.data_visita.desc()).offset(offset).limit(limit).all()


@router.post("/visitas", response_model=VisitaOut, status_code=status.HTTP_201_CREATED)
def create_visita(payload: VisitaCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    visita = PastoralVisita(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(visita); db.commit(); db.refresh(visita)
    return visita


@router.patch("/visitas/{visita_id}", response_model=VisitaOut)
def update_visita(visita_id: int, payload: VisitaUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    visita = db.query(PastoralVisita).filter(PastoralVisita.id == visita_id, PastoralVisita.tenant_id == current_user.tenant_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita nÃ£o encontrada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(visita, k, v)
    db.commit(); db.refresh(visita)
    return visita


@router.delete("/visitas/{visita_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visita(visita_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    visita = db.query(PastoralVisita).filter(PastoralVisita.id == visita_id, PastoralVisita.tenant_id == current_user.tenant_id).first()
    if not visita:
        raise HTTPException(status_code=404, detail="Visita nÃ£o encontrada")
    db.delete(visita); db.commit()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# Aconselhamentos CRUD
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.get("/aconselhamentos", response_model=list[AconselhamentoOut])
def list_aconselhamentos(
    membro_id: int | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(PastoralAconselhamento).filter(PastoralAconselhamento.tenant_id == current_user.tenant_id)
    if membro_id is not None:
        q = q.filter(PastoralAconselhamento.membro_id == membro_id)
    return q.order_by(PastoralAconselhamento.data_sessao.desc()).offset(offset).limit(limit).all()


@router.post("/aconselhamentos", response_model=AconselhamentoOut, status_code=status.HTTP_201_CREATED)
def create_aconselhamento(payload: AconselhamentoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = PastoralAconselhamento(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.patch("/aconselhamentos/{item_id}", response_model=AconselhamentoOut)
def update_aconselhamento(item_id: int, payload: AconselhamentoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PastoralAconselhamento).filter(PastoralAconselhamento.id == item_id, PastoralAconselhamento.tenant_id == current_user.tenant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Aconselhamento nÃ£o encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.commit(); db.refresh(item)
    return item


@router.delete("/aconselhamentos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aconselhamento(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(PastoralAconselhamento).filter(PastoralAconselhamento.id == item_id, PastoralAconselhamento.tenant_id == current_user.tenant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Aconselhamento nÃ£o encontrado")
    db.delete(item); db.commit()
