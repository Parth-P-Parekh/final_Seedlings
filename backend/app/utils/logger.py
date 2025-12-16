# Logging utilities - to be filled from logger_py.txt
import logging
from rich.logging import RichHandler
from rich.console import Console
from app.core.config import settings

# Create console for Rich output
console = Console()


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with Rich handler for pretty output.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=False,
            console=console
        )

        formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(settings.LOG_LEVEL)

    return logger