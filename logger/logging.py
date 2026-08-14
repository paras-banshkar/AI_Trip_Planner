import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"trip_planner_{datetime.now().strftime('%Y-%m-%d')}.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str = "ai_trip_planner") -> logging.Logger:
    """
    Returns a configured module-level logger that writes to both a
    rotating log file (so logs don't grow unbounded) and stdout.

    Usage:
        from logger.logging import get_logger
        logger = get_logger(__name__)
        logger.info("something happened")
    """
    logger = logging.getLogger(name)

    # Avoid attaching duplicate handlers if get_logger() is called more
    # than once for the same logger name (e.g. across module reloads).
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
