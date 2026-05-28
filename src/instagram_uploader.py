"""
Instagram Uploader — handles login, session management, and video uploads
as Reels using the instagrapi library.
"""

import random
import time
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    ClientError,
)

from .config import (
    INSTAGRAM_USERNAME,
    INSTAGRAM_PASSWORD,
    IG_SESSION_FILE,
    APP_LOG_FILE,
)
from .logger import setup_logger

logger = setup_logger(APP_LOG_FILE)


class InstagramUploader:
    """Manages Instagram login sessions and video uploads."""

    def __init__(self):
        self.client = Client()
        self._logged_in = False

        # Set realistic device/user-agent settings to reduce detection
        self.client.delay_range = [1, 3]

    def login(self) -> bool:
        """
        Log in to Instagram, reusing a saved session if available.

        Returns:
            True if login was successful, False otherwise.
        """
        # Try to load existing session
        if IG_SESSION_FILE.exists():
            try:
                logger.info("Loading saved Instagram session...")
                self.client.load_settings(str(IG_SESSION_FILE))
                self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

                # Verify the session is still valid
                self.client.get_timeline_feed()
                logger.info(f"[OK] Instagram session restored for @{INSTAGRAM_USERNAME}")
                self._logged_in = True
                return True
            except (LoginRequired, ChallengeRequired, ClientError) as e:
                logger.warning(f"Saved session expired or invalid: {e}")
                logger.info("Attempting fresh login...")
                # Delete stale session
                IG_SESSION_FILE.unlink(missing_ok=True)

        # Fresh login
        try:
            logger.info(f"Logging into Instagram as @{INSTAGRAM_USERNAME}...")
            self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

            # Save session for future runs
            IG_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(IG_SESSION_FILE))
            logger.info("[OK] Instagram login successful. Session saved.")
            self._logged_in = True
            return True

        except TwoFactorRequired:
            logger.error(
                "Instagram requires 2FA verification. "
                "Please disable 2FA temporarily, or enter the code manually."
            )
            try:
                code = input("Enter Instagram 2FA code: ").strip()
                self.client.two_factor_login(code)
                self.client.dump_settings(str(IG_SESSION_FILE))
                logger.info("[OK] 2FA login successful. Session saved.")
                self._logged_in = True
                return True
            except Exception as e:
                logger.error(f"2FA login failed: {e}")
                return False

        except ChallengeRequired:
            logger.error(
                "Instagram challenge required (suspicious login detected). "
                "Please log in manually via the Instagram app to verify, "
                "then try again."
            )
            return False

        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False

    def upload_reel(
        self, video_path: Path, caption: str = ""
    ) -> tuple[bool, str, str]:
        """
        Upload a video as an Instagram Reel.

        Args:
            video_path: Path to the video file
            caption: Caption text for the reel

        Returns:
            Tuple of (success: bool, media_id: str, error_message: str)
        """
        if not self._logged_in:
            if not self.login():
                return False, "", "Not logged in to Instagram"

        if not video_path.exists():
            return False, "", f"Video file not found: {video_path}"

        logger.info(f"[>>] Uploading to Instagram: {caption[:60]}...")
        logger.info(f"  File: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")

        # Add a small random delay before upload (mimic human behavior)
        delay = random.uniform(2, 5)
        logger.debug(f"  Pre-upload delay: {delay:.1f}s")
        time.sleep(delay)

        try:
            media = self.client.clip_upload(
                path=str(video_path),
                caption=caption,
            )

            media_id = str(media.pk)
            logger.info(f"[OK] Instagram Reel uploaded! Media ID: {media_id}")
            logger.info(f"  -> https://www.instagram.com/reel/{media.code}/")

            # Save updated session
            self.client.dump_settings(str(IG_SESSION_FILE))

            return True, media_id, ""

        except LoginRequired:
            logger.warning("Session expired during upload. Re-authenticating...")
            IG_SESSION_FILE.unlink(missing_ok=True)
            self._logged_in = False

            if self.login():
                # Retry once after re-login
                try:
                    media = self.client.clip_upload(
                        path=str(video_path),
                        caption=caption,
                    )
                    media_id = str(media.pk)
                    logger.info(f"[OK] Instagram Reel uploaded (after re-login)! Media ID: {media_id}")
                    return True, media_id, ""
                except Exception as e:
                    error_msg = f"Upload failed after re-login: {e}"
                    logger.error(error_msg)
                    return False, "", error_msg
            else:
                return False, "", "Failed to re-authenticate with Instagram"

        except Exception as e:
            error_msg = f"Instagram upload error: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

    def logout(self):
        """Log out and clean up."""
        if self._logged_in:
            try:
                self.client.logout()
                logger.info("Logged out of Instagram.")
            except Exception:
                pass  # Ignore logout errors
            self._logged_in = False
