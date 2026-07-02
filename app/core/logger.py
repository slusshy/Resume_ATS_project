"""Logging utilities."""

import logging

from app.core.config import settings

logger = logging.getLogger("recruitermind")
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
