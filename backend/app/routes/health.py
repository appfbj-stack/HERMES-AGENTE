from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "ok",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
