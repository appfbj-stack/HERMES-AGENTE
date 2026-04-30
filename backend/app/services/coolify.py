import httpx
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import User

logger = get_logger(__name__)


async def coolify_deploy(
    db: Session,
    user: User,
    application_id: str,
    branch: Optional[str] = None,
    force_rebuild: bool = False,
) -> dict:
    settings = get_settings()
    if not settings.coolify_api_key:
        return {"success": False, "error": "Coolify API key not configured"}
    if not settings.coolify_api_base_url:
        return {"success": False, "error": "Coolify API base URL not configured"}

    url = f"{settings.coolify_api_base_url}/api/v1/applications/{application_id}/deploy"
    headers = {"Authorization": f"Bearer {settings.coolify_api_key}", "Content-Type": "application/json"}

    payload = {}
    if branch:
        payload["branch"] = branch
    if force_rebuild:
        payload["forceRebuild"] = True

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"success": True, "deployment": response.json()}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Coolify deploy failed for application_id=%s: %s", application_id, exc)
            return {"success": False, "error": str(exc)}


async def coolify_trigger_webhook(
    db: Session,
    user: User,
    webhook_url: str,
    payload: Optional[dict] = None,
) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(webhook_url, json=payload or {})
            response.raise_for_status()
            return {"success": True, "status": "triggered"}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Coolify webhook trigger failed for url=%s: %s", webhook_url, exc)
            return {"success": False, "error": str(exc)}


async def coolify_get_status(
    db: Session,
    user: User,
    application_id: str,
) -> dict:
    settings = get_settings()
    if not settings.coolify_api_key:
        return {"success": False, "error": "Coolify API key not configured"}
    if not settings.coolify_api_base_url:
        return {"success": False, "error": "Coolify API base URL not configured"}

    url = f"{settings.coolify_api_base_url}/api/v1/applications/{application_id}"
    headers = {"Authorization": f"Bearer {settings.coolify_api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {"success": True, "application": response.json()}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Coolify status lookup failed for application_id=%s: %s", application_id, exc)
            return {"success": False, "error": str(exc)}


async def coolify_get_deployments(
    db: Session,
    user: User,
    application_id: str,
    limit: int = 10,
) -> dict:
    settings = get_settings()
    if not settings.coolify_api_key:
        return {"success": False, "error": "Coolify API key not configured"}
    if not settings.coolify_api_base_url:
        return {"success": False, "error": "Coolify API base URL not configured"}

    url = f"{settings.coolify_api_base_url}/api/v1/applications/{application_id}/deployments"
    headers = {"Authorization": f"Bearer {settings.coolify_api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers, params={"limit": limit})
            response.raise_for_status()
            return {"success": True, "deployments": response.json()}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Coolify deployment history lookup failed for application_id=%s: %s", application_id, exc)
            return {"success": False, "error": str(exc)}
