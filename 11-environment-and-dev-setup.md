# 11 — Environment & Dev Setup
## Telegram Job Search AI Agent

---

## 1. Prerequisites

| Tool | Version | Check Command | Install |
|---|---|---|---|
| Python | 3.10+ | `python --version` | python.org |
| pip | Latest | `pip --version` | Comes with Python |
| Git | Any | `git --version` | git-scm.com |
| VS Code | Any | — | code.visualstudio.com |
| Telegram Account | — | — | telegram.org |
| RapidAPI Account | — | — | rapidapi.com |

---

## 2. Project Structure

```
C:\Users\Amresh kumar\Downloads\AI\
│
├── bot.py                 # Main bot (run this)
├── job_searcher.py        # Job search engine
├── requirements.txt       # Python packages
├── .env                   # Your API keys (PRIVATE)
├── .env.example           # Template (safe to share)
└── README.md              # Setup guide
```

---

## 3. Step-by-Step Setup

### Step 1: Get Telegram Bot Token

```
1. Telegram खोलो
2. Search करो: @BotFather
3. /newbot type करो
4. Bot का नाम दो (e.g.: "My Job Finder Bot")
5. Username दो (e.g.: "myjobfinder_bot") — must end in "bot"
6. Token मिलेगा:
   → 7123456789:ABCdefGHIjklMNOpqrSTUvwxYZ-abc

⚠️ Warning: यह token किसी को मत दो!
```

---

### Step 2: Get RapidAPI Key (JSearch)

```
1. https://rapidapi.com पर जाओ
2. Free account बनाओ
3. Search करो: "JSearch"
4. JSearch by letscrape लिखी API select करो
5. "Subscribe to Test" click करो (Free plan select करो)
6. Dashboard में जाओ → "Apps" → "default-application"
7. API Key copy करो (X-RapidAPI-Key)
```

🔗 Direct link: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

---

### Step 3: Configure `.env` File

`.env` file open करो (already created है) और अपनी keys डालो:

```env
TELEGRAM_BOT_TOKEN=7123456789:ABCdefGHIjklMNOpqrSTUvwxYZ-abc
RAPIDAPI_KEY=abc123def456ghi789jkl012mno345pqr
```

**Important:**
- कोई quotes मत लगाओ ( `"` या `'` )
- Copy-paste exactly as-is
- No spaces around `=`

---

### Step 4: Install Dependencies

Terminal/Command Prompt खोलो:

```bash
# AI folder में जाओ
cd "C:\Users\Amresh kumar\Downloads\AI"

# Install all packages
pip install -r requirements.txt
```

Expected output:
```
Successfully installed httpx-0.28.1 python-dotenv-1.0.1 python-telegram-bot-21.3
```

---

### Step 5: Run the Bot

```bash
python bot.py
```

Expected output:
```
🤖 Telegram Job Search Bot starting...
✅ Press Ctrl+C to stop
🟢 Bot is live! Telegram pe /start karo
```

---

### Step 6: Test in Telegram

1. Telegram खोलो
2. अपना bot search करो (username से)
3. `/start` भेजो
4. Job query type करो: `Python Developer Mumbai`
5. Results देखो! 🎉

---

## 4. Environment Variables Reference

| Variable | Required | Description | Example |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | BotFather से मिला token | `7123...:ABCdef...` |
| `RAPIDAPI_KEY` | ✅ | RapidAPI का API key | `abc123def456...` |

---

## 5. Common Development Commands

```bash
# Bot start करो
python bot.py

# Bot बंद करो
Ctrl + C

# Dependencies install करो
pip install -r requirements.txt

# Python version check करो
python --version

# Installed packages देखो
pip list

# .env file test करो (keys load हो रही हैं?)
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token:', os.getenv('TELEGRAM_BOT_TOKEN')[:20] + '...' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET')"
```

---

## 6. VS Code Setup (Recommended)

### Extensions Install करो:
- **Python** (Microsoft) — Python language support
- **Pylance** — Better intellisense
- **indent-rainbow** — Better indentation visibility
- **.env** support — Syntax highlight in .env files

### VS Code Settings (`settings.json`):
```json
{
    "python.defaultInterpreterPath": "python",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

---

## 7. How to Run on a VPS (24/7) — Phase 2

### Option A: Systemd Service (Linux VPS)

```bash
# /etc/systemd/system/job-bot.service
[Unit]
Description=Telegram Job Search Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AI
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/AI/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable job-bot
sudo systemctl start job-bot
sudo systemctl status job-bot

# View logs
journalctl -u job-bot -f
```

---

### Option B: Screen / tmux (Simple)

```bash
# Start in background
screen -S jobbot
python bot.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r jobbot
```

---

### Option C: Docker (Phase 2)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
# Build and run
docker build -t job-bot .
docker run -d --env-file .env --name job-bot job-bot

# Check logs
docker logs job-bot -f
```

---

## 8. Environments

| Environment | Setup | Use Case |
|---|---|---|
| **Local** | `python bot.py` on your PC | Development & Testing |
| **VPS (Linux)** | Systemd service | 24/7 production |
| **Heroku/Railway** | Procfile + env vars | Free cloud hosting |
| **Docker** | Docker run | Consistent deployment |

---

## 9. Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `TELEGRAM_BOT_TOKEN not set` | .env missing or wrong key name | Check .env file, no quotes |
| `RAPIDAPI_KEY not set` | Same | Same |
| `ModuleNotFoundError: telegram` | python-telegram-bot not installed | `pip install -r requirements.txt` |
| `HTTP 401 Unauthorized` | Wrong bot token | Get fresh token from BotFather |
| `HTTP 429 Too Many Requests` | RapidAPI limit exceeded | Upgrade plan or wait |
| `Timeout Error` | Internet slow or API down | Check internet, try again |
| `Conflict: terminated by other getUpdates` | Two bots running same token | Close other terminal |
| `IndentationError` | Python spacing wrong | Use spaces, not tabs |

---

## 10. Security Checklist

- [ ] `.env` file added to `.gitignore` ← Most important!
- [ ] Bot token never committed to GitHub
- [ ] RapidAPI key never committed to GitHub
- [ ] `.env.example` (with dummy values) is what you share

### `.gitignore` file:
```
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
venv/
```
