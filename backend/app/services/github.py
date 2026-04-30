import httpx
from git import Repo, Actor
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import User

logger = get_logger(__name__)


async def github_commit(
    db: Session,
    user: User,
    message: str,
    files: Optional[list[str]] = None,
    author_name: Optional[str] = None,
    author_email: Optional[str] = None,
) -> dict:
    settings = get_settings()
    if not settings.github_token:
        return {"success": False, "error": "GitHub token not configured"}
    if not settings.github_owner or not settings.github_repo:
        return {"success": False, "error": "GitHub owner/repo not configured"}

    try:
        repo_path = f"./repos/{user.tenant_id}"
        repo = Repo(repo_path)

        if files:
            repo.index.add(files)
        else:
            repo.index.add("*")

        actor = Actor(author_name or "Hermes Bot", author_email or "bot@hermes.com")
        commit = repo.index.commit(message, author=actor, committer=actor)

        return {
            "success": True,
            "commit_hash": commit.hexsha,
            "message": message,
            "author": str(actor),
        }
    except (GitCommandError, InvalidGitRepositoryError, NoSuchPathError, OSError, ValueError) as exc:
        logger.warning("GitHub commit helper failed for tenant_id=%s: %s", user.tenant_id, exc)
        return {"success": False, "error": str(exc)}


async def github_push(
    db: Session,
    user: User,
    branch: str = "main",
) -> dict:
    settings = get_settings()
    if not settings.github_token:
        return {"success": False, "error": "GitHub token not configured"}
    if not settings.github_owner or not settings.github_repo:
        return {"success": False, "error": "GitHub owner/repo not configured"}

    try:
        repo_path = f"./repos/{user.tenant_id}"
        repo = Repo(repo_path)

        origin = repo.remote(name="origin")
        origin.push(branch)

        return {"success": True, "branch": branch}
    except (GitCommandError, InvalidGitRepositoryError, NoSuchPathError, OSError, ValueError) as exc:
        logger.warning("GitHub push helper failed for tenant_id=%s branch=%s: %s", user.tenant_id, branch, exc)
        return {"success": False, "error": str(exc)}


async def github_create_pull_request(
    db: Session,
    user: User,
    title: str,
    body: str,
    head: str,
    base: str = "main",
) -> dict:
    settings = get_settings()
    if not settings.github_token:
        return {"success": False, "error": "GitHub token not configured"}

    url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/pulls"
    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    payload = {"title": title, "body": body, "head": head, "base": base}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"success": True, "pr": response.json()}
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("GitHub PR creation failed for tenant_id=%s head=%s base=%s: %s", user.tenant_id, head, base, exc)
            return {"success": False, "error": str(exc)}
