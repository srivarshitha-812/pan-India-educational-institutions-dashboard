"""
Logging configuration for the system.
"""
import logging
import sys
from datetime import datetime
from config import LOG_DIR

def setup_logger(name: str = "education_collector", log_file: str = None) -> logging.Logger:
    """Configures and returns a logger instance with console and file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_file is None:
        log_file = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_path = LOG_DIR / log_file
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

logger = setup_logger()
