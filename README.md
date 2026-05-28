# 📹 Auto Video Uploader

> Auto Video Uploader is a robust Python utility that automates your daily social media workflow. It schedules and uploads local video files directly to YouTube and Instagram Reels. Built with duplicate prevention, resumable YouTube uploads, and session persistence, this tool ensures your content reaches your audience without manual effort.

---

## 📑 Table of Contents

- [Features](#-features)
- [Quick Setup (5 minutes)](#-quick-setup-5-minutes)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Configuration Options](#-configuration-options)
- [Important Notes](#-important-notes)
- [Troubleshooting](#-troubleshooting)

---

## 🌟 Features

- 🎬 **Multi-Platform Support**: Uploads videos to both YouTube and Instagram Reels automatically.
- 📋 **Duplicate Tracking**: Tracks which videos have been uploaded so it never posts the same content twice.
- ⏰ **Automated Scheduling**: Set up a daily schedule or run on-demand whenever you have new content.
- 🔄 **Resumable Uploads**: Handles large files & network issues gracefully for YouTube.
- 🔐 **Session Persistence**: No need to log in repeatedly; authentication sessions are saved securely.
- 📊 **Upload Statistics**: Built-in status checks and logs to monitor your upload history.
- 📝 **Rotating Log Files**: Detailed logs that automatically manage their own file size.

---

## 🚀 Quick Setup (5 minutes)

### 1. Install Python Dependencies

Open a terminal and install the required Python packages:

```bash
cd D:\auto-uploader
pip install -r requirements.txt
```

### 2. Configure YouTube API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. **Create a new project** (or select an existing one).
3. Go to **APIs & Services → Library**.
4. Search for **"YouTube Data API v3"** and **Enable** it.
5. Go to **APIs & Services → Credentials**.
6. Click **Create Credentials → OAuth 2.0 Client ID**.
   - Application type: **Desktop app**
   - Name: anything (e.g., "Auto Uploader")
7. Click **Download JSON** and save it as:
   ```
   D:\auto-uploader\config\client_secrets.json
   ```
8. Go to **APIs & Services → OAuth consent screen**.
   - Add your email as a **Test User**.

### 3. Authorize YouTube (one-time)

Run the initial setup script to authenticate with YouTube:

```bash
python setup_youtube.py
```

This will open your browser for Google sign-in. Authorize the app, and a token will be saved automatically for future use.

### 4. Configure Instagram & Settings

Copy the provided example environment file and add your credentials:

```bash
copy config\.env.example config\.env
```

Edit `config\.env` and fill in your details:

```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
VIDEOS_FOLDER=D:\videos
VIDEOS_PER_DAY=1
YT_PRIVACY=public
UPLOAD_TIME=09:00
```

### 5. Test It!

You can test your configuration without actually uploading anything:

```bash
# Preview what would be uploaded (no actual upload)
python src/main.py --dry-run

# Check current statistics and status
python src/main.py --status
```

---

## 💻 Usage

### Upload Now
```bash
python src/main.py --now
```
Picks the next un-uploaded video(s) and uploads them to both platforms immediately.

### Daily Schedule (Daemon)
```bash
python src/main.py --schedule
```
Runs continuously in the background and uploads at the configured time each day. Press `Ctrl+C` to stop the script.

### Windows Task Scheduler (Recommended for Daily)

Instead of keeping a Python process running constantly, you can use Windows Task Scheduler:

1. Open **Task Scheduler** on Windows.
2. Click **Create Task**.
3. **General**: Name it "Daily Video Uploader".
4. **Triggers**: New → Daily → Set your preferred time.
5. **Actions**: New → Start a program.
   - **Program**: `python` (or full path to `python.exe`)
   - **Arguments**: `src/main.py --now`
   - **Start in**: `D:\auto-uploader`
6. Click OK.

Alternatively, you can configure the task via PowerShell:
```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "src/main.py --now" -WorkingDirectory "D:\auto-uploader"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00AM"
Register-ScheduledTask -TaskName "DailyVideoUploader" -Action $action -Trigger $trigger -Description "Upload videos to YouTube and Instagram daily"
```

---

## 📁 Project Structure

```
auto-uploader/
├── config/
│   ├── .env                    ← Your credentials (DO NOT SHARE)
│   ├── .env.example            ← Template for .env
│   ├── client_secrets.json     ← YouTube OAuth credentials
│   ├── token.json              ← Auto-generated YouTube token
│   └── ig_session.json         ← Auto-generated Instagram session
├── logs/
│   ├── upload_log.json         ← Tracks uploaded videos
│   └── uploader.log            ← Application logs
├── src/
│   ├── main.py                 ← Entry point
│   ├── youtube_uploader.py     ← YouTube upload logic
│   ├── instagram_uploader.py   ← Instagram upload logic
│   ├── video_manager.py        ← Video selection & tracking
│   ├── config.py               ← Configuration loader
│   └── logger.py               ← Logging setup
├── setup_youtube.py            ← One-time YouTube OAuth setup
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration Options

Here is a breakdown of what you can configure inside your `config\.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `INSTAGRAM_USERNAME` | *(required)* | Your Instagram username |
| `INSTAGRAM_PASSWORD` | *(required)* | Your Instagram password |
| `VIDEOS_FOLDER` | `D:\videos` | Path to your local videos folder |
| `VIDEOS_PER_DAY` | `1` | Videos to upload per day (per platform) |
| `YT_PRIVACY` | `public` | YouTube privacy setting: `public`, `unlisted`, `private` |
| `YT_CATEGORY_ID` | `22` | YouTube category (22 = People & Blogs) |
| `YT_DEFAULT_DESCRIPTION` | *(empty)* | Default description applied to all YouTube uploads |
| `YT_DEFAULT_TAGS` | *(empty)* | Comma-separated list of default tags |
| `UPLOAD_TIME` | `09:00` | Daily upload time in 24h format |
| `UPLOAD_DELAY_MIN` | `30` | Minimum seconds to wait between multiple video uploads |
| `UPLOAD_DELAY_MAX` | `120` | Maximum seconds to wait between multiple video uploads |

---

## ⚠️ Important Notes

### YouTube Quota Limits
- The YouTube API has a strict daily quota of **10,000 units**.
- Each video upload costs **1,600 units**.
- This allows a maximum of **6 uploads per day** using the default quota.
- Your API quota resets at midnight Pacific Time (PT).

### Instagram Safety Guidelines
- Instagram is sensitive to automated bot activity.
- Start small with **1 video/day** and increase gradually over time.
- Use your Instagram account manually on your phone for a few days before enabling full automation.
- If you encounter a "Challenge Required" error, log into the Instagram app on your phone, complete the check, and try again.

### Supported Video Formats
The script currently supports `.mp4`, `.mov`, `.avi`, `.mkv`, and `.webm` formats.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **"client_secrets.json not found"** | You need to download it from the Google Cloud Console (Refer to Setup Step 2). |
| **"YouTube quota exceeded"** | You've hit the 6 videos/day limit. Wait until midnight PT, or request a quota increase from Google. |
| **"Instagram challenge required"** | Open the Instagram app on your mobile device, log in, complete the security challenge, and run the script again. |
| **"Instagram 2FA required"** | Check your terminal for a prompt to enter your 2FA code, or temporarily disable 2FA for the account. |
| **Videos not being picked up** | Ensure your videos match the supported extensions and the `VIDEOS_FOLDER` path in your `.env` is correct. |
| **Old videos are re-uploading** | Check `logs/upload_log.json` to ensure tracking data isn't being deleted or corrupted. |
#   A u t o - V i d e o - U p l o a d e r  
 #   A u t o - V i d e o - U p l o a d e r  
 