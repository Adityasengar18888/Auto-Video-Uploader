"""
YouTube Uploader — handles OAuth authentication and video uploads
using the YouTube Data API v3.
"""

import http.client
import httplib2
import random
import time
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import (
    YT_CLIENT_SECRETS,
    YT_TOKEN_FILE,
    YT_PRIVACY,
    YT_CATEGORY_ID,
    YT_DEFAULT_DESCRIPTION,
    YT_DEFAULT_TAGS,
)
from .logger import setup_logger
from .config import APP_LOG_FILE

logger = setup_logger(APP_LOG_FILE)

# OAuth scope for uploading videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Retry settings for resumable uploads
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                         http.client.IncompleteRead, http.client.ImproperConnectionState,
                         http.client.CannotSendRequest, http.client.CannotSendHeader,
                         http.client.ResponseNotReady, http.client.BadStatusLine)


def _get_authenticated_service():
    """
    Build and return an authenticated YouTube API service.
    Uses saved token if available, otherwise prompts for OAuth login.
    """
    creds = None

    # Load existing token
    if YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), SCOPES)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired YouTube token...")
            creds.refresh(Request())
        else:
            if not YT_CLIENT_SECRETS.exists():
                logger.error(f"client_secrets.json not found at: {YT_CLIENT_SECRETS}")
                logger.error("Run setup_youtube.py first to configure OAuth.")
                return None

            logger.info("Starting YouTube OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(YT_CLIENT_SECRETS), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        YT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(YT_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        logger.info("YouTube token saved.")

    return build("youtube", "v3", credentials=creds)


def _resumable_upload(request) -> str:
    """
    Execute a resumable upload with exponential backoff retry logic.

    Returns:
        The YouTube video ID on success, or empty string on failure.
    """
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            logger.info("Uploading chunk...")
            status, response = request.next_chunk()
            if response is not None:
                if "id" in response:
                    video_id = response["id"]
                    logger.info(f"[OK] YouTube upload complete! Video ID: {video_id}")
                    logger.info(f"  -> https://www.youtube.com/watch?v={video_id}")
                    return video_id
                else:
                    logger.error(f"Upload failed with unexpected response: {response}")
                    return ""
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP error {e.resp.status}: {e.content.decode()}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = str(e)

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                logger.error(f"Max retries exceeded. Last error: {error}")
                return ""

            sleep_seconds = random.random() * (2 ** retry)
            logger.warning(f"Retry {retry}/{MAX_RETRIES} in {sleep_seconds:.1f}s — {error}")
            time.sleep(sleep_seconds)

    return ""


def upload_video(
    video_path: Path,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    privacy: str = "",
    category_id: str = "",
) -> tuple[bool, str, str]:
    """
    Upload a video to YouTube.

    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description (uses default from config if empty)
        tags: List of tags (uses defaults from config if None)
        privacy: Privacy status (uses config default if empty)
        category_id: YouTube category ID (uses config default if empty)

    Returns:
        Tuple of (success: bool, video_id: str, error_message: str)
    """
    if not video_path.exists():
        return False, "", f"Video file not found: {video_path}"

    # Apply defaults
    description = description or YT_DEFAULT_DESCRIPTION
    tags = tags if tags is not None else YT_DEFAULT_TAGS
    privacy = privacy or YT_PRIVACY
    category_id = category_id or YT_CATEGORY_ID

    logger.info(f"[>>] Uploading to YouTube: {title}")
    logger.info(f"  File: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
    logger.info(f"  Privacy: {privacy} | Category: {category_id}")

    try:
        youtube = _get_authenticated_service()
        if youtube is None:
            return False, "", "Failed to authenticate with YouTube"

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/*",
            resumable=True,
            chunksize=1024 * 1024 * 10,  # 10 MB chunks
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        video_id = _resumable_upload(request)
        if video_id:
            return True, video_id, ""
        else:
            return False, "", "Upload completed but no video ID returned"

    except HttpError as e:
        error_msg = f"YouTube API error: {e.resp.status} — {e.content.decode()}"
        logger.error(error_msg)
        return False, "", error_msg

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return False, "", error_msg
