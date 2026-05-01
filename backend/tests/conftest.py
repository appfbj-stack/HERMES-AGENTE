import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-with-at-least-32-chars")

from app.core.security import get_password_hash
from app.models import Base, Chat, Credit, Tenant, TenantModule, User


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tenant(
    db: Session,
    *,
    name: str,
    email: str,
    plan: str = "pro",
    active: bool = True,
    modules: dict[str, bool] | None = None,
    credits: int = 100,
) -> Tenant:
    tenant = Tenant(name=name, email=email, plan=plan, active=active)
    db.add(tenant)
    db.flush()
    db.add(Credit(tenant_id=tenant.id, total=credits, used=0, remaining=credits))
    db.add(TenantModule(tenant_id=tenant.id, **(modules or {})))
    db.flush()
    return tenant


def create_user(
    db: Session,
    *,
    tenant_id: int,
    name: str,
    email: str,
    password: str = "Senha123!",
    role: str = "admin",
    is_super_admin: bool = False,
) -> User:
    user = User(
        tenant_id=tenant_id,
        name=name,
        email=email,
        password=get_password_hash(password),
        role=role,
        is_super_admin=is_super_admin,
    )
    db.add(user)
    db.flush()
    return user


def create_chat(
    db: Session,
    *,
    tenant_id: int,
    external_id: str,
    channel: str = "web",
    contact_name: str = "Contato",
    contact_phone: str | None = None,
) -> Chat:
    chat = Chat(
        tenant_id=tenant_id,
        channel=channel,
        chat_external_id=external_id,
        contact_name=contact_name,
        contact_phone=contact_phone,
        status="open",
    )
    db.add(chat)
    db.flush()
    return chat
