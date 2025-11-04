"""Structured logging configuration using structlog."""

import sys
import logging
from pathlib import Path
from typing import Any
import structlog
from structlog.typing import EventDict, WrappedLogger

from app.core.config import settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log entries."""
    event_dict["app_name"] = settings.app.name
    event_dict["app_version"] = settings.app.version
    event_dict["env"] = settings.app.env
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Ensure log directory exists
    settings.storage.log_path.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.app.debug else logging.INFO,
    )

    # Configure file handler
    log_file = settings.storage.log_path / "app.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(file_handler)

    # Configure error log file
    error_log_file = settings.storage.log_path / "error.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(error_handler)

    # Configure structlog
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    if settings.app.debug:
        # Development: use console renderer with colors
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: use JSON renderer
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()
