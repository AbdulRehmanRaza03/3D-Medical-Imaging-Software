"""Centralized logging configuration."""
from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger for structured, single-handler output."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers when reloading under uvicorn --reload.
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
