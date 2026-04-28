import os
import aiofiles
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import User


async def list_files(
    db: Session,
    user: User,
    path: str = "./",
    pattern: Optional[str] = None,
) -> dict:
    try:
        base_path = Path(path).resolve()
        if not base_path.exists():
            return {"success": False, "error": "Path does not exist"}

        files = []
        if pattern:
            files = list(base_path.glob(pattern))
        else:
            files = list(base_path.rglob("*"))

        result = []
        for f in files:
            if f.is_file():
                stat = f.stat()
                result.append(
                    {
                        "name": f.name,
                        "path": str(f.relative_to(base_path)),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )

        return {"success": True, "files": result, "total": len(result)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def read_file(
    db: Session,
    user: User,
    path: str,
    encoding: str = "utf-8",
) -> dict:
    try:
        file_path = Path(path).resolve()
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}
        if not file_path.is_file():
            return {"success": False, "error": "Path is not a file"}

        async with aiofiles.open(file_path, mode="r", encoding=encoding) as f:
            content = await f.read()

        return {"success": True, "content": content, "size": len(content)}
    except UnicodeDecodeError:
        return {"success": False, "error": "File encoding not supported"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def write_file(
    db: Session,
    user: User,
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> dict:
    try:
        file_path = Path(path).resolve()
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
            await f.write(content)

        return {"success": True, "path": str(file_path), "size": len(content)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def delete_file(
    db: Session,
    user: User,
    path: str,
) -> dict:
    try:
        file_path = Path(path).resolve()
        if not file_path.exists():
            return {"success": False, "error": "File does not exist"}

        if file_path.is_dir():
            os.rmdir(file_path)
        else:
            os.remove(file_path)

        return {"success": True, "path": str(file_path)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
