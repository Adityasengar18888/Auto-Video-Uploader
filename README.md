# 📹 Auto Video Uploader

Automate video uploads to **YouTube** and **Instagram Reels** using Python.

This project provides a reliable workflow for creators who want to schedule and publish local video files automatically with duplicate prevention, resumable uploads, logging, and session persistence.

---

# ✨ Features

* 🎬 Upload videos to YouTube and Instagram Reels
* 📅 Automated daily scheduling
* 🔄 Resumable YouTube uploads
* 🧠 Duplicate upload prevention
* 🔐 Persistent login sessions
* 📊 Upload tracking & statistics
* 📝 Rotating logs for monitoring
* ⚡ Simple CLI commands

---

# 📂 Project Structure

```text
auto-uploader/
│
├── config/
│   ├── .env.example
│   ├── client_secrets.json
│   ├── token.json
│   └── ig_session.json
│
├── logs/
│   ├── upload_log.json
│   └── uploader.log
│
├── src/
│   ├── main.py
│   ├── youtube_uploader.py
│   ├── instagram_uploader.py
│   ├── video_manager.py
│   ├── config.py
│   └── logger.py
│
├── setup_youtube.py
├── requirements.txt
└── README.md
```

---

# ⚡ Quick Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Adityasengar18888/Auto-Video-Uploader.git

cd Auto-Video-Uploader
```

---

## 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 YouTube API Setup

## Enable YouTube API

1. Open Google Cloud Console
2. Create a project
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 Desktop Credentials
5. Download credentials JSON

Place the file here:

```text
config/client_secrets.json
```

---

## Authenticate YouTube

```bash
python setup_youtube.py
```

A browser window will open for Google login.

---

# ⚙️ Environment Configuration

Copy example environment file:

```bash
copy config\.env.example config\.env
```

Edit `.env`:

```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

VIDEOS_FOLDER=D:\videos

VIDEOS_PER_DAY=1

YT_PRIVACY=public

UPLOAD_TIME=09:00
```

---

# 🚀 Usage

## Upload Immediately

```bash
python src/main.py --now
```

---

## Dry Run

Preview uploads without actually posting:

```bash
python src/main.py --dry-run
```

---

## Show Status

```bash
python src/main.py --status
```

---

## Start Daily Scheduler

```bash
python src/main.py --schedule
```

---

# 🪟 Windows Task Scheduler (Recommended)

Instead of running continuously, use Windows Task Scheduler.

## PowerShell Setup

```powershell
$action = New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "src/main.py --now" `
    -WorkingDirectory "D:\auto-uploader"

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "09:00AM"

Register-ScheduledTask `
    -TaskName "DailyVideoUploader" `
    -Action $action `
    -Trigger $trigger
```

---

# ⚙️ Configuration Options

| Variable             | Description                 |
| -------------------- | --------------------------- |
| `INSTAGRAM_USERNAME` | Instagram username          |
| `INSTAGRAM_PASSWORD` | Instagram password          |
| `VIDEOS_FOLDER`      | Folder containing videos    |
| `VIDEOS_PER_DAY`     | Upload limit per day        |
| `YT_PRIVACY`         | public / private / unlisted |
| `UPLOAD_TIME`        | Daily upload time           |

---

# 📦 Supported Formats

* `.mp4`
* `.mov`
* `.avi`
* `.mkv`
* `.webm`

---

# ⚠️ Important Notes

## YouTube API Quota

* Daily quota: **10,000 units**
* One upload: **1,600 units**
* Approx max uploads/day: **6**

---

## Instagram Automation Safety

* Start slowly (1 upload/day)
* Avoid aggressive automation
* Complete any Instagram security challenges manually if prompted

---

# 🛠️ Troubleshooting

| Problem                         | Solution                                     |
| ------------------------------- | -------------------------------------------- |
| `client_secrets.json not found` | Download OAuth credentials from Google Cloud |
| `quotaExceeded`                 | Wait for quota reset                         |
| `Instagram challenge required`  | Login manually on mobile app                 |
| Videos not detected             | Check `VIDEOS_FOLDER` path                   |

---

# 🔒 Security

Never upload these files to GitHub:

```text
config/token.json
config/client_secrets.json
config/.env
```

Add them to `.gitignore`.

---

# 📜 License

This project is for educational and personal automation purposes.

---

# 👨‍💻 Author

Developed by Aditya Sengar 🚀
