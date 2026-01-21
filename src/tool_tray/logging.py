import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_logger: logging.Logger | None = None


def get_log_dir() -> Path:
    """Get OS-appropriate log directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "tooltray/logs"
        return Path.home() / "AppData/Local/tooltray/logs"
    elif sys.platform == "darwin":
        return Path.home() / "Library/Logs/tooltray"
    else:
        return Path.home() / ".local/state/tooltray/log"


def get_logger() -> logging.Logger:
    """Get or create the tooltray logger."""
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("tooltray")
    _logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if _logger.handlers:
        return _logger

    # File handler with rotation (1MB, keep 3 files)
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "tooltray.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    # Format: timestamp - level - message
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    return _logger


def log_info(msg: str) -> None:
    """Log info message."""
    get_logger().info(msg)


def log_error(msg: str, exc: Exception | None = None) -> None:
    """Log error message with optional exception."""
    logger = get_logger()
    if exc:
        logger.error(f"{msg}: {exc}", exc_info=True)
    else:
        logger.error(msg)


def log_debug(msg: str) -> None:
    """Log debug message."""
    get_logger().debug(msg)
