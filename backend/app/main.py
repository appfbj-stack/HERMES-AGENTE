from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.chats import router as chats_router
from app.routes.credits import router as credits_router
from app.routes.health import router as health_router
from app.routes.leads import router as leads_router
from app.routes.messages import router as messages_router
from app.routes.tasks import router as tasks_router
from app.routes.webhook import router as webhook_router

settings = get_settings()

app = FastAPI(title="Hermes Agente API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(leads_router)
app.include_router(tasks_router)
app.include_router(credits_router)
app.include_router(webhook_router)

