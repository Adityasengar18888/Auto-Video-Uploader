"""
Main Orchestrator -- entry point for the Auto-Uploader.

Modes:
    --now       Upload immediately (pick next batch of videos)
    --schedule  Run as a daemon, uploading daily at the configured time
    --status    Show upload statistics
    --dry-run   Show which videos would be uploaded without actually uploading
"""

import argparse
import random
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    VIDEOS_PER_DAY,
    UPLOAD_TIME,
    UPLOAD_DELAY_MIN,
    UPLOAD_DELAY_MAX,
    APP_LOG_FILE,
    validate,
)
from src.logger import setup_logger
from src.video_manager import (
    get_next_videos,
    mark_uploaded,
    title_from_filename,
    get_stats,
)
from src.youtube_uploader import upload_video as yt_upload
from src.instagram_uploader import InstagramUploader

logger = setup_logger(APP_LOG_FILE)


def print_banner():
    """Print a nice startup banner."""
    print()
    print("  +=============================================+")
    print("  |       [*] Auto Video Uploader v1.0          |")
    print("  |     YouTube + Instagram Daily Uploads       |")
    print("  +=============================================+")
    print()


def show_status():
    """Display current upload statistics."""
    stats = get_stats()
    print(f"  [STATS] Upload Statistics")
    print(f"  ----------------------------------")
    print(f"  Total videos:          {stats['total_videos']}")
    print(f"  YouTube uploaded:      {stats['youtube_uploaded']}")
    print(f"  Instagram uploaded:    {stats['instagram_uploaded']}")
    print(f"  Fully uploaded (both): {stats['fully_uploaded']}")
    print(f"  Remaining:             {stats['remaining']}")
    print()


def do_upload_batch(dry_run: bool = False):
    """
    Upload the next batch of videos to both platforms.

    Args:
        dry_run: If True, just show what would be uploaded without uploading.
    """
    videos = get_next_videos(VIDEOS_PER_DAY)

    if not videos:
        logger.info("[DONE] All videos have been uploaded! Nothing to do.")
        return

    logger.info(f"[QUEUE] Selected {len(videos)} video(s) for upload:")
    for i, v in enumerate(videos, 1):
        title = title_from_filename(v)
        size_mb = v.stat().st_size / 1024 / 1024
        logger.info(f"   {i}. {title} ({size_mb:.1f} MB)")

    if dry_run:
        logger.info("(Dry run -- no uploads will be performed)")
        return

    print()

    # Initialize Instagram client once for the batch
    ig_uploader = InstagramUploader()

    for i, video_path in enumerate(videos):
        title = title_from_filename(video_path)
        logger.info(f"{'=' * 60}")
        logger.info(f"Processing [{i + 1}/{len(videos)}]: {title}")
        logger.info(f"{'=' * 60}")

        # --- YouTube Upload ---
        logger.info("")
        logger.info("[YT] YouTube Upload")
        logger.info("-" * 40)
        try:
            success, video_id, error = yt_upload(video_path, title)
            if success:
                mark_uploaded(video_path.name, "youtube", "success", media_id=video_id)
                logger.info(f"[OK] YouTube: SUCCESS (ID: {video_id})")
            else:
                mark_uploaded(video_path.name, "youtube", "failed", error=error)
                logger.error(f"[FAIL] YouTube: FAILED -- {error}")
        except Exception as e:
            mark_uploaded(video_path.name, "youtube", "failed", error=str(e))
            logger.error(f"[FAIL] YouTube: CRASHED -- {e}")

        # Small delay between platforms
        delay = random.uniform(5, 15)
        logger.debug(f"  Waiting {delay:.0f}s before Instagram upload...")
        time.sleep(delay)

        # --- Instagram Upload ---
        logger.info("")
        logger.info("[IG] Instagram Upload")
        logger.info("-" * 40)
        try:
            success, media_id, error = ig_uploader.upload_reel(video_path, caption=title)
            if success:
                mark_uploaded(video_path.name, "instagram", "success", media_id=media_id)
                logger.info(f"[OK] Instagram: SUCCESS (ID: {media_id})")
            else:
                mark_uploaded(video_path.name, "instagram", "failed", error=error)
                logger.error(f"[FAIL] Instagram: FAILED -- {error}")
        except Exception as e:
            mark_uploaded(video_path.name, "instagram", "failed", error=str(e))
            logger.error(f"[FAIL] Instagram: CRASHED -- {e}")

        # Delay between videos (if more than one)
        if i < len(videos) - 1:
            delay = random.uniform(UPLOAD_DELAY_MIN, UPLOAD_DELAY_MAX)
            logger.info(f"\n[WAIT] Waiting {delay:.0f}s before next video...\n")
            time.sleep(delay)

    # Cleanup
    ig_uploader.logout()

    # Show final stats
    print()
    show_status()
    logger.info("[DONE] Upload batch complete!")


def run_scheduler():
    """Run as a long-lived process, uploading daily at the configured time."""
    try:
        import schedule
    except ImportError:
        logger.error("'schedule' package not installed. Run: pip install schedule")
        sys.exit(1)

    logger.info(f"[SCHED] Scheduler started. Will upload daily at {UPLOAD_TIME}")
    logger.info("   Press Ctrl+C to stop.")
    print()

    schedule.every().day.at(UPLOAD_TIME).do(do_upload_batch)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user.")


def main():
    """Parse arguments and run the appropriate mode."""
    print_banner()

    parser = argparse.ArgumentParser(
        description="Auto Video Uploader -- Upload videos to YouTube & Instagram daily",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py --now          Upload the next batch immediately
  python src/main.py --schedule     Run as daemon (uploads daily at configured time)
  python src/main.py --status       Show upload statistics
  python src/main.py --dry-run      Preview which videos would be uploaded
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--now", action="store_true", help="Upload immediately")
    group.add_argument("--schedule", action="store_true", help="Run daily at configured time")
    group.add_argument("--status", action="store_true", help="Show upload statistics")
    group.add_argument("--dry-run", action="store_true", help="Preview next uploads without uploading")

    args = parser.parse_args()

    # Validate config (except for status which doesn't need full validation)
    if not args.status:
        if not validate():
            logger.error("Fix the configuration errors above and try again.")
            sys.exit(1)

    if args.status:
        show_status()
    elif args.dry_run:
        do_upload_batch(dry_run=True)
    elif args.now:
        do_upload_batch()
    elif args.schedule:
        run_scheduler()


if __name__ == "__main__":
    main()
