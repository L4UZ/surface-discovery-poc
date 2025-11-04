"""Logging configuration"""
import logging
import sys
from rich.logging import RichHandler
from rich.console import Console


def setup_logger(name: str, verbose: bool = False) -> logging.Logger:
    """Setup logger with rich handler"""
    logger = logging.getLogger(name)

    # Set level
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Add rich handler
    handler = RichHandler(
        console=Console(stderr=True),
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
        show_time=True,
        show_path=verbose
    )
    handler.setLevel(level)

    # Format
    formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
