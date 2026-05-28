"""
Configuration loader for the Auto-Uploader.
Loads settings from .env file and provides typed access to all config values.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


# Resolve paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"

# Load .env file
_env_path = CONFIG_DIR / ".env"
if not _env_path.exists():
    print(f"[ERROR] .env file not found at: {_env_path}")
    print(f"        Copy config/.env.example to config/.env and fill in your credentials.")
    sys.exit(1)

load_dotenv(_env_path)


def _get_required(key: str) -> str:
    """Get a required environment variable or exit with an error."""
    value = os.getenv(key)
    if not value:
        print(f"[ERROR] Required config '{key}' is not set in .env")
        sys.exit(1)
    return value


def _get_optional(key: str, default: str = "") -> str:
    """Get an optional environment variable with a default."""
    return os.getenv(key, default)


# ---------------------
# Instagram
# ---------------------
INSTAGRAM_USERNAME = _get_required("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = _get_required("INSTAGRAM_PASSWORD")

# ---------------------
# Video Settings
# ---------------------
VIDEOS_FOLDER = Path(_get_optional("VIDEOS_FOLDER", r"D:\videos"))
VIDEOS_PER_DAY = int(_get_optional("VIDEOS_PER_DAY", "1"))

# ---------------------
# YouTube Settings
# ---------------------
YT_PRIVACY = _get_optional("YT_PRIVACY", "public")
YT_CATEGORY_ID = _get_optional("YT_CATEGORY_ID", "22")
YT_DEFAULT_DESCRIPTION = _get_optional("YT_DEFAULT_DESCRIPTION", "")
YT_DEFAULT_TAGS = [
    tag.strip()
    for tag in _get_optional("YT_DEFAULT_TAGS", "").split(",")
    if tag.strip()
]

# YouTube OAuth files
YT_CLIENT_SECRETS = CONFIG_DIR / "client_secrets.json"
YT_TOKEN_FILE = CONFIG_DIR / "token.json"

# ---------------------
# Schedule Settings
# ---------------------
UPLOAD_TIME = _get_optional("UPLOAD_TIME", "09:00")
UPLOAD_DELAY_MIN = int(_get_optional("UPLOAD_DELAY_MIN", "30"))
UPLOAD_DELAY_MAX = int(_get_optional("UPLOAD_DELAY_MAX", "120"))

# ---------------------
# Log / State files
# ---------------------
UPLOAD_LOG_FILE = LOGS_DIR / "upload_log.json"
APP_LOG_FILE = LOGS_DIR / "uploader.log"
IG_SESSION_FILE = CONFIG_DIR / "ig_session.json"

# ---------------------
# Supported video extensions
# ---------------------
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def validate(require_youtube: bool = True):
    """
    Validate that all required files and directories exist.

    Args:
        require_youtube: If False, skip YouTube credential check (for dry-run mode).
    """
    errors = []
    warnings = []

    if not VIDEOS_FOLDER.exists():
        errors.append(f"Videos folder not found: {VIDEOS_FOLDER}")

    if not YT_CLIENT_SECRETS.exists():
        if require_youtube:
            errors.append(
                f"YouTube client_secrets.json not found: {YT_CLIENT_SECRETS}\n"
                f"  -> Download it from Google Cloud Console > APIs & Services > Credentials"
            )
        else:
            warnings.append(
                f"YouTube client_secrets.json not found (YouTube uploads will be skipped)"
            )

    if warnings:
        print("\n[WARNINGS]")
        for w in warnings:
            print(f"  [!] {w}")
        print()

    if errors:
        print("\n[CONFIG ERRORS]")
        for err in errors:
            print(f"  [X] {err}")
        print()
        return False

    return True
