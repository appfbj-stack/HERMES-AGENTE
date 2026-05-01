import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

FILE_HANDLER_NAME = "hermes_file"
CONSOLE_HANDLER_NAME = "hermes_console"


def _configure_handler(handler: logging.Handler, formatter: logging.Formatter, name: str) -> None:
    handler.set_name(name)
    handler.setFormatter(formatter)


def setup_logging(log_level: str = "INFO") -> None:
    """Configura logging centralizado com arquivo e console."""

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for handler in root_logger.handlers:
        if handler.get_name() in {FILE_HANDLER_NAME, CONSOLE_HANDLER_NAME}:
            handler.setLevel(root_logger.level)
            handler.setFormatter(formatter)
            return

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(root_logger.level)
    _configure_handler(file_handler, formatter, FILE_HANDLER_NAME)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(root_logger.level)
    _configure_handler(console_handler, formatter, CONSOLE_HANDLER_NAME)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger com o nome especificado."""
    return logging.getLogger(name)
