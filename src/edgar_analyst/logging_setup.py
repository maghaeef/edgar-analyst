"""Logging setup for edgar_analyst.

Uses rich for colored, structured terminal output. Call `get_logger` from
any module — handler attachment is idempotent so repeated calls are safe.
"""

import logging
from rich.logging import RichHandler

_CONFIGURED = False


def get_logger(name: str = "edgar_analyst") -> logging.Logger:
    """Return a logger configured with a RichHandler.

    The first call configures the root handler for the package; subsequent
    calls return child loggers that inherit that configuration.

    Args:
        name: Logger name. Pass `__name__` from the calling module to get
            a properly-namespaced child logger.

    Returns:
        Configured logger instance.
    """
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
        )
        _CONFIGURED = True
    return logging.getLogger(name)