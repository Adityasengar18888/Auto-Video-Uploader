"""
Logging setup for the Auto-Uploader.
Provides both console (colored) and file logging with rotation.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""

    COLORS = {
        logging.DEBUG: Fore.CYAN if HAS_COLORAMA else "",
        logging.INFO: Fore.GREEN if HAS_COLORAMA else "",
        logging.WARNING: Fore.YELLOW if HAS_COLORAMA else "",
        logging.ERROR: Fore.RED if HAS_COLORAMA else "",
        logging.CRITICAL: Fore.RED + Style.BRIGHT if HAS_COLORAMA else "",
    }
    RESET = Style.RESET_ALL if HAS_COLORAMA else ""

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)


def setup_logger(log_file: Path, name: str = "auto-uploader") -> logging.Logger:
    """
    Configure and return a logger that writes to both console and a rotating log file.

    Args:
        log_file: Path to the log file
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # --- File handler (rotating, 5MB per file, keep 3 backups) ---
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # --- Console handler (colored) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
