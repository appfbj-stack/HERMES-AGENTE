import os
import aiofiles
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models import User

logger = get_logger(__name__)


async def list_social_files(
    db: Session,
    user: User,
    pattern: Optional[str] = None,
    subfolder: Optional[str] = None,
) -> dict:
    try:
        settings = get_settings()
        social_path = Path(settings.social_files_path).resolve()

        if not social_path.exists():
            social_path.mkdir(parents=True, exist_ok=True)

        if subfolder:
            social_path = social_path / subfolder
            if not social_path.exists():
                social_path.mkdir(parents=True, exist_ok=True)

        files = []
        if pattern:
            files = list(social_path.glob(pattern))
        else:
            files = list(social_path.rglob("*"))

        result = []
        for f in files:
            if f.is_file():
                stat = f.stat()
                result.append(
                    {
                        "name": f.name,
                        "path": str(f.relative_to(social_path)),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )

        return {"success": True, "files": result, "total": len(result)}
    except (OSError, ValueError) as exc:
        logger.warning("Social file listing failed for user_id=%s subfolder=%s: %s", user.id, subfolder, exc)
        return {"success": False, "error": str(exc)}


async def read_social_file(
    db: Session,
    user: User,
    filename: str,
    subfolder: Optional[str] = None,
    encoding: str = "utf-8",
) -> dict:
    try:
        settings = get_settings()
        social_path = Path(settings.social_files_path).resolve()

        if subfolder:
            social_path = social_path / subfolder

        file_path = social_path / filename
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}
        if not file_path.is_file():
            return {"success": False, "error": "Path is not a file"}

        async with aiofiles.open(file_path, mode="r", encoding=encoding) as f:
            content = await f.read()

        return {"success": True, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        return {"success": False, "error": "File encoding not supported"}
    except (OSError, ValueError) as exc:
        logger.warning("Social file read failed for user_id=%s filename=%s: %s", user.id, filename, exc)
        return {"success": False, "error": str(exc)}


async def write_social_file(
    db: Session,
    user: User,
    filename: str,
    content: str,
    subfolder: Optional[str] = None,
    encoding: str = "utf-8",
) -> dict:
    try:
        settings = get_settings()
        social_path = Path(settings.social_files_path).resolve()
        social_path.mkdir(parents=True, exist_ok=True)

        if subfolder:
            social_path = social_path / subfolder
            social_path.mkdir(parents=True, exist_ok=True)

        file_path = social_path / filename

        async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
            await f.write(content)

        return {"success": True, "path": str(file_path), "size": len(content)}
    except (OSError, ValueError) as exc:
        logger.warning("Social file write failed for user_id=%s filename=%s: %s", user.id, filename, exc)
        return {"success": False, "error": str(exc)}


async def delete_social_file(
    db: Session,
    user: User,
    filename: str,
    subfolder: Optional[str] = None,
) -> dict:
    try:
        settings = get_settings()
        social_path = Path(settings.social_files_path).resolve()

        if subfolder:
            social_path = social_path / subfolder

        file_path = social_path / filename
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}

        os.remove(file_path)

        return {"success": True, "path": str(file_path)}
    except (OSError, ValueError) as exc:
        logger.warning("Social file delete failed for user_id=%s filename=%s: %s", user.id, filename, exc)
        return {"success": False, "error": str(exc)}
