# 07 — Component Structure
## Telegram Job Search AI Agent

---

## 1. Project Directory Structure

```
AI/                                      # Project root
│
├── bot.py                               # 🤖 Main Telegram bot + all handlers
├── job_searcher.py                      # 🔍 Job search logic (JSearch API)
│
├── requirements.txt                     # 📦 Python dependencies
├── .env                                 # 🔑 API keys (YOUR actual keys)
├── .env.example                         # 📋 Keys template (share this, not .env)
├── README.md                            # 📖 Setup & usage guide
│
└── docs/                                # 📄 (Optional) documentation folder
    ├── 01-product-requirements.md
    ├── 02-user-stories-and-acceptance-criteria.md
    ├── 03-information-architecture.md
    ├── 04-system-architecture.md
    ├── 05-database-schema.md
    ├── 06-api-contracts.md
    ├── 07-component-structure.md
    ├── 08-scoring-engine-spec.md
    ├── 09-engineering-scope-definition.md
    ├── 10-development-phases.md
    ├── 11-environment-and-dev-setup.md
    └── 12-testing-strategy.md
```

---

## 2. `bot.py` — Component Breakdown

### 2.1 Imports & Initialization

```python
# Telegram library
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ...
from telegram.constants import ParseMode, ChatAction

# Our module
from job_searcher import JobSearcher

# Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Singleton
searcher = JobSearcher(api_key=RAPIDAPI_KEY)

# In-memory state
user_sessions: dict = {}
```

---

### 2.2 Command Handlers

| Handler Function | Command | Responsibility |
|---|---|---|
| `start()` | `/start` | Welcome message, bot intro, example queries |
| `help_command()` | `/help` | Detailed usage guide, all commands |
| `trending_jobs()` | `/trending` | Pre-set popular query, 5 trending results |
| `search_command()` | `/search [args]` | Parse args, delegate to `perform_search()` |
| `clear_session()` | `/clear` | Delete user from `user_sessions` dict |

---

### 2.3 Message Handler

```python
async def handle_message(update, context):
    """
    Called for every non-command text message.
    Flow:
      1. Get user text
      2. Validate length (> 2 chars)
      3. Call perform_search()
    """
```

---

### 2.4 Core Search Orchestrator

```python
async def perform_search(update, context, query: str):
    """
    Central search function called by all entry points.
    
    Flow:
      1. Send "Searching..." message
      2. Show TYPING action
      3. Call searcher.search_jobs(query)
      4. Handle empty results
      5. Save to user_sessions
      6. Delete "Searching..." message
      7. Send header message
      8. Loop through first 5 jobs → send each card
      9. Send "Load More" if > 5 results
    """
```

---

### 2.5 Callback Handler

```python
async def callback_handler(update, context):
    """
    Handles inline keyboard button presses.
    
    Callback data formats:
      "page_1_{user_id}"  → load page 2 (jobs 6-8)
      "new_search"        → prompt user for new query
    """
```

---

### 2.6 Formatting Functions

```python
def format_job_card(job: dict, index: int) -> str:
    """
    Converts job dict to Telegram Markdown string.
    
    Handles:
      - Markdown special characters escaped
      - Description truncated to 300 chars
      - Rating suffix if available
      - Posted date suffix if available
    
    Returns: Markdown string
    """

def format_job_card_plain(job: dict, index: int) -> str:
    """
    Plain text fallback if Markdown parsing fails.
    Used in try/except around reply_text.
    
    Returns: Plain string (no formatting)
    """

def build_job_keyboard(job: dict) -> InlineKeyboardMarkup:
    """
    Creates inline keyboard for each job card.
    
    Buttons:
      Row 1: [Apply Now] (if apply_url) + [Company] (if company_url)
      Row 2: [🔍 Naya Search] (always)
    
    Returns: InlineKeyboardMarkup
    """
```

---

### 2.7 Error Handler

```python
async def error_handler(update, context):
    """
    Global error handler for unhandled exceptions.
    - Logs full traceback
    - Sends user-friendly error message
    - Bot continues running (doesn't crash)
    """
```

---

## 3. `job_searcher.py` — Component Breakdown

### 3.1 Class: `JobSearcher`

```python
class JobSearcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
```

---

### 3.2 Public Method: `search_jobs()`

```
Input:  query (str), num_results (int)
          ↓
_enhance_query(query)
          ↓
httpx.AsyncClient.get(JSearch API)
          ↓
Parse response.json()
          ↓
_parse_job() for each raw job
          ↓
Output: list[dict] (clean job objects)
```

---

### 3.3 Private Methods

| Method | Input | Output | Purpose |
|---|---|---|---|
| `_enhance_query()` | raw query (str) | enhanced query (str) | Adds "India" if no location |
| `_parse_job()` | raw API dict | clean job dict or None | Extract all fields |
| `_parse_salary()` | raw API dict | salary string | Format ₹8L - ₹12L |
| `_format_number()` | float, currency (str) | "8L" / "80K" | INR/USD formatting |
| `_clean_description()` | raw text (str) | clean text (str) | Remove HTML, limit chars |
| `_format_posted_date()` | ISO date string | "2 din pehle" | Human-readable date |
| `_get_source()` | raw API dict | "LinkedIn" / "Indeed" | Source platform name |

---

## 4. Data Flow Between Components

```
User Text
    │
    ▼
bot.py: handle_message()
    │
    ▼
bot.py: perform_search(query)
    │
    ├─→ bot.send_chat_action(TYPING)
    │
    ├─→ job_searcher.search_jobs(query)
    │       │
    │       ├─→ _enhance_query(query)
    │       ├─→ httpx.get(JSearch API)
    │       ├─→ _parse_job(raw) × N
    │       │       ├─→ _parse_salary(raw)
    │       │       ├─→ _clean_description(text)
    │       │       └─→ _format_posted_date(date)
    │       └─→ returns [job1, job2, ...]
    │
    ├─→ user_sessions[user_id] = {...}
    │
    └─→ for each job:
            format_job_card(job, i)
            build_job_keyboard(job)
            update.message.reply_text(...)
```

---

## 5. Configuration (`config.py` — Phase 2)

Phase 2 mein settings ko centralize karenge:

```python
# config.py
from dataclasses import dataclass

@dataclass
class Config:
    # Bot
    TELEGRAM_BOT_TOKEN: str
    RAPIDAPI_KEY: str
    
    # Search defaults
    MAX_RESULTS: int = 8
    RESULTS_PER_PAGE: int = 5
    API_TIMEOUT_SECONDS: int = 20
    MESSAGE_DELAY_SECONDS: float = 0.4
    
    # Query enhancement
    DEFAULT_LOCATION: str = "India"
    LOCATION_KEYWORDS: list = None
    
    # Description
    MAX_DESCRIPTION_CHARS: int = 300
    MAX_DESCRIPTION_FULL_CHARS: int = 400
    
    # Session
    SESSION_EXPIRE_HOURS: int = 1
```

---

## 6. Future Components (Phase 2 & 3)

### Phase 2 Additions

```
AI/
├── bot.py                  # Enhanced with alert commands
├── job_searcher.py         # Cache layer added
├── alert_scheduler.py      # NEW: APScheduler for daily alerts
├── database.py             # NEW: SQLite ORM (aiosqlite)
├── config.py               # NEW: Centralized config
└── utils/
    ├── formatters.py       # Extracted format functions
    ├── validators.py       # Query validation
    └── logger.py           # Custom structured logging
```

### Phase 3 Additions

```
AI/
├── services/
│   ├── job_service.py      # Business logic layer
│   ├── user_service.py     # User management
│   └── alert_service.py    # Alert management
├── repositories/
│   ├── user_repo.py        # DB access for users
│   ├── search_repo.py      # DB access for searches
│   └── alert_repo.py       # DB access for alerts
├── api/
│   └── webhook.py          # FastAPI webhook server
├── Dockerfile              # Container image
├── docker-compose.yml      # Local dev with PostgreSQL
└── kubernetes/             # K8s deployment manifests
```
