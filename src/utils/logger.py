"""Structured logging setup based on loguru.

Import ``log`` anywhere in the project:

    from src.utils.logger import log
    log.info("ingested {} rows", n)
"""

from __future__ import annotations

import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    ),
)
logger.add(
    "logs/pipeline_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="10 MB",
    retention="14 days",
    serialize=False,
)

log = logger
