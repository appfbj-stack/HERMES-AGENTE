from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from . import models  # noqa: F401 - registra os modelos
from .routers import auth, chats, leads, tasks, credits, webhooks


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente SaaS", version="1.0.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(leads.router)
app.include_router(tasks.router)
app.include_router(credits.router)
app.include_router(webhooks.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "agente-saas", "env": settings.environment}


@app.get("/health")
def health():
    return {"status": "ok", "service": "agente-saas", "env": settings.environment}
