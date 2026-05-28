"""
Video Manager — scans the videos folder, tracks upload history,
and picks the next batch of un-uploaded videos.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import VIDEOS_FOLDER, UPLOAD_LOG_FILE, VIDEO_EXTENSIONS


def _load_log() -> dict:
    """Load the upload log from disk."""
    if UPLOAD_LOG_FILE.exists():
        try:
            with open(UPLOAD_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"uploads": []}
    return {"uploads": []}


def _save_log(data: dict):
    """Save the upload log to disk."""
    UPLOAD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(UPLOAD_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def scan_videos() -> list[Path]:
    """
    Scan the videos folder and return a sorted list of video file paths.
    Sorted alphabetically for consistent ordering.
    """
    if not VIDEOS_FOLDER.exists():
        return []

    videos = [
        f for f in VIDEOS_FOLDER.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
    return sorted(videos, key=lambda p: p.name.lower())


def get_uploaded_filenames(platform: Optional[str] = None) -> set[str]:
    """
    Get the set of filenames that have been successfully uploaded.

    Args:
        platform: If specified ('youtube' or 'instagram'), only return files
                  successfully uploaded to that platform. If None, return files
                  uploaded to ALL platforms.
    """
    log = _load_log()
    uploaded = set()

    for entry in log["uploads"]:
        filename = entry["filename"]

        if platform is None:
            # Consider uploaded only if both platforms succeeded
            yt_ok = entry.get("youtube", {}).get("status") == "success"
            ig_ok = entry.get("instagram", {}).get("status") == "success"
            if yt_ok and ig_ok:
                uploaded.add(filename)
        elif platform == "youtube":
            if entry.get("youtube", {}).get("status") == "success":
                uploaded.add(filename)
        elif platform == "instagram":
            if entry.get("instagram", {}).get("status") == "success":
                uploaded.add(filename)

    return uploaded


def get_next_videos(count: int = 1) -> list[Path]:
    """
    Get the next N videos that haven't been uploaded to BOTH platforms yet.

    Videos are selected in alphabetical order. A video is considered
    'pending' if it hasn't been successfully uploaded to at least one platform.
    """
    all_videos = scan_videos()
    yt_uploaded = get_uploaded_filenames("youtube")
    ig_uploaded = get_uploaded_filenames("instagram")

    # A video needs uploading if it's missing from either platform
    fully_uploaded = yt_uploaded & ig_uploaded
    pending = [v for v in all_videos if v.name not in fully_uploaded]

    return pending[:count]


def get_upload_status(filename: str) -> dict:
    """Get the upload status for a specific video file."""
    log = _load_log()
    for entry in log["uploads"]:
        if entry["filename"] == filename:
            return entry
    return {}


def mark_uploaded(filename: str, platform: str, status: str,
                  media_id: str = "", error: str = ""):
    """
    Record that a video was uploaded (or failed) on a platform.

    Args:
        filename: Name of the video file
        platform: 'youtube' or 'instagram'
        status: 'success' or 'failed'
        media_id: Platform-specific media/video ID (on success)
        error: Error message (on failure)
    """
    log = _load_log()

    # Find existing entry or create new one
    entry = None
    for e in log["uploads"]:
        if e["filename"] == filename:
            entry = e
            break

    if entry is None:
        entry = {"filename": filename}
        log["uploads"].append(entry)

    # Update platform status
    entry[platform] = {
        "status": status,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    if media_id:
        entry[platform]["media_id"] = media_id
    if error:
        entry[platform]["error"] = error

    _save_log(log)


def title_from_filename(filepath: Path) -> str:
    """
    Derive a clean title/caption from a video filename.
    Strips the extension and cleans up common artifacts.
    """
    name = filepath.stem  # filename without extension
    # Keep the name as-is — many of these have meaningful titles
    return name.strip()


def get_stats() -> dict:
    """Get overall upload statistics."""
    all_videos = scan_videos()
    log = _load_log()

    total = len(all_videos)
    yt_done = len(get_uploaded_filenames("youtube"))
    ig_done = len(get_uploaded_filenames("instagram"))
    both_done = len(get_uploaded_filenames(None))

    return {
        "total_videos": total,
        "youtube_uploaded": yt_done,
        "instagram_uploaded": ig_done,
        "fully_uploaded": both_done,
        "remaining": total - both_done,
    }
