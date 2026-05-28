"""
YouTube OAuth Setup Script.
Run this once to authorize the app to upload videos to your YouTube channel.
This will open a browser window for Google OAuth consent.

Usage:
    python setup_youtube.py
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from src.config import YT_CLIENT_SECRETS, YT_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("=" * 60)
    print("  YouTube OAuth Setup")
    print("=" * 60)
    print()

    # Check for client_secrets.json
    if not YT_CLIENT_SECRETS.exists():
        print(f"  ✗ ERROR: client_secrets.json not found!")
        print(f"    Expected location: {YT_CLIENT_SECRETS}")
        print()
        print("  To get this file:")
        print("    1. Go to https://console.cloud.google.com/")
        print("    2. Create a new project (or select existing)")
        print("    3. Enable 'YouTube Data API v3'")
        print("    4. Go to APIs & Services > Credentials")
        print("    5. Create OAuth 2.0 Client ID (Desktop app)")
        print("    6. Download the JSON and save it as:")
        print(f"       {YT_CLIENT_SECRETS}")
        print()
        sys.exit(1)

    # Check if already authorized
    if YT_TOKEN_FILE.exists():
        print("  Found existing token. Checking if it's still valid...")
        creds = Credentials.from_authorized_user_file(str(YT_TOKEN_FILE), SCOPES)

        if creds and creds.valid:
            print("  ✓ Token is already valid! You're all set.")
            return

        if creds and creds.expired and creds.refresh_token:
            print("  Token expired. Refreshing...")
            try:
                creds.refresh(Request())
                with open(YT_TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                print("  ✓ Token refreshed successfully!")
                return
            except Exception as e:
                print(f"  ✗ Refresh failed: {e}")
                print("  Starting fresh OAuth flow...")

    # Run OAuth flow
    print("  Opening browser for Google OAuth authorization...")
    print("  (If the browser doesn't open, check the terminal for a URL)")
    print()

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(YT_CLIENT_SECRETS), SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Save the token
        YT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(YT_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

        print()
        print("  ✓ Authorization successful!")
        print(f"  ✓ Token saved to: {YT_TOKEN_FILE}")
        print()
        print("  You can now run the auto-uploader.")
        print("  The token will auto-refresh when it expires.")

    except Exception as e:
        print(f"\n  ✗ Authorization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
