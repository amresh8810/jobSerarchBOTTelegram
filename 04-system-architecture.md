# 04 — System Architecture
## Telegram Job Search AI Agent

---

## 1. Architecture Overview

यह system एक **simple, stateless Python application** है जो Telegram Bot API और JSearch REST API को bridge करता है। MVP में कोई database नहीं है — sessions in-memory रहते हैं।

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER LAYER                               │
│           📱 Telegram App (iOS / Android / Desktop)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (Telegram API)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  TELEGRAM SERVERS                            │
│              api.telegram.org                                │
│         (Webhook / Long Polling)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ Updates (messages, callbacks)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  BOT APPLICATION                             │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │                   bot.py                            │    │
│   │                                                     │    │
│   │  CommandHandlers    MessageHandler    CallbackHandler│   │
│   │  /start /help       Plain text        Inline buttons│   │
│   │  /search /trending  → search()        → page nav    │   │
│   │  /clear             ↓                               │   │
│   │                     perform_search()                │   │
│   │                     ↓                               │   │
│   │              format_job_card()                      │   │
│   │              build_job_keyboard()                   │   │
│   └─────────────────────┬──────────────────────────────┘   │
│                         │                                    │
│   ┌─────────────────────▼──────────────────────────────┐    │
│   │                job_searcher.py                      │    │
│   │                                                     │    │
│   │  search_jobs()          _enhance_query()            │   │
│   │  _parse_job()           _parse_salary()             │   │
│   │  _clean_description()   _format_posted_date()       │   │
│   └─────────────────────┬──────────────────────────────┘   │
│                         │ HTTP (httpx async)                 │
│   user_sessions{}       │                                    │
│   (In-Memory Dict)      │                                    │
└─────────────────────────┼────────────────────────────────────┘
                           │ HTTPS REST API Call
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  JSEARCH API (RapidAPI)                      │
│         jsearch.p.rapidapi.com/search                        │
│                                                              │
│   Sources: LinkedIn | Indeed | Glassdoor | ZipRecruiter      │
│            Naukri | Monster | SimplyHired                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 `bot.py` — Telegram Interface Layer

**Responsibilities:**
- Telegram Bot API connection (python-telegram-bot library)
- Command routing (`/start`, `/help`, `/search`, `/trending`, `/clear`)
- Plain text message handler → triggers search
- Inline keyboard button callbacks
- Message formatting and sending
- User session management (in-memory dict)
- Error handler

**Key Functions:**
| Function | Purpose |
|---|---|
| `start()` | /start command → welcome message |
| `help_command()` | /help → usage guide |
| `trending_jobs()` | /trending → pre-defined popular search |
| `search_command()` | /search [args] → direct search |
| `handle_message()` | Any text → job search |
| `perform_search()` | Core search orchestrator |
| `callback_handler()` | Inline button press handler |
| `format_job_card()` | Job dict → Markdown message |
| `build_job_keyboard()` | Create Apply/Company buttons |

---

### 3.2 `job_searcher.py` — Search Engine Layer

**Responsibilities:**
- JSearch API HTTP calls (async via httpx)
- Query enhancement for better results
- Raw API response parsing
- Salary extraction and formatting
- Description cleaning

**Key Functions:**
| Function | Purpose |
|---|---|
| `search_jobs()` | Main search → returns list of job dicts |
| `_enhance_query()` | Adds "India" if no location in query |
| `_parse_job()` | Raw API dict → clean job dict |
| `_parse_salary()` | Extract salary from various fields |
| `_format_number()` | Numbers → ₹8L / $80K format |
| `_clean_description()` | Remove HTML, limit to 400 chars |
| `_format_posted_date()` | ISO date → "2 din pehle" |

---

### 3.3 `user_sessions{}` — In-Memory State

```python
user_sessions: dict = {
    123456789: {          # Telegram user_id
        "query": "Python Developer Mumbai",
        "results": [...], # List of job dicts
        "page": 0         # For pagination
    }
}
```

**Lifecycle:**
- Created on first search
- Updated on each new search (replaces old)
- Read on "Load More" button click
- Deleted via `/clear` command

---

## 4. Data Flow — Complete Search Request

```
Step 1:  User types "React Developer Bangalore" in Telegram
Step 2:  Telegram sends Update to bot (long polling)
Step 3:  handle_message() receives the text
Step 4:  perform_search() called with query="React Developer Bangalore"
Step 5:  Bot sends "🔍 Searching... ⏳" message
Step 6:  JobSearcher.search_jobs() called
Step 7:  _enhance_query() → "React Developer Bangalore" (no change, has location)
Step 8:  httpx async GET → jsearch.p.rapidapi.com/search?query=React+Developer+Bangalore
Step 9:  API returns raw JSON (list of jobs)
Step 10: _parse_job() called for each raw job → clean dict
Step 11: List of clean jobs returned to perform_search()
Step 12: Session saved: user_sessions[user_id] = {query, results, page:0}
Step 13: "Searching..." message deleted
Step 14: Header message sent: "✅ 8 jobs mile!"
Step 15: For each of first 5 jobs:
          - format_job_card() → Markdown string
          - build_job_keyboard() → InlineKeyboardMarkup
          - bot.send_message() → Telegram
Step 16: If len(results) > 5: "Load More" button sent
```

---

## 5. Technology Stack

| Layer | Technology | Version | Why |
|---|---|---|---|
| Language | Python | 3.10+ | Async support, readability |
| Bot Framework | python-telegram-bot | 21.x | Production-grade, async native |
| HTTP Client | httpx | 0.28+ | Async HTTP, modern API |
| Job Search API | JSearch (RapidAPI) | v1 | Multi-platform aggregator |
| Env Management | python-dotenv | 1.0+ | 12-factor app config |
| Concurrency | asyncio | Built-in | Non-blocking I/O |

---

## 6. Deployment Architecture (MVP)

```
┌──────────────────────────────────────┐
│        Your Local Machine /          │
│        VPS / Cloud VM                │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  Python Process                │  │
│  │  python bot.py                 │  │
│  │                                │  │
│  │  Long Polling (default)        │  │
│  │  Bot polls Telegram every Xs   │  │
│  └────────────────────────────────┘  │
│                                      │
│  .env (API Keys)                     │
└──────────────────────────────────────┘
        │                   ↕
        │           Telegram Servers
        │           api.telegram.org
        │
        └──→ RapidAPI (JSearch)
             jsearch.p.rapidapi.com
```

### Future Production Deployment

```
GitHub → CI/CD → Docker Image → Cloud Run / AWS EC2
                                      │
                                Webhook mode (faster)
                                      │
                              Telegram Webhook endpoint
```

---

## 7. Error Handling Architecture

```
API Call
    ↓
try:
    response = await httpx.get(...)
    response.raise_for_status()
except httpx.TimeoutException:
    → log + return []
except httpx.HTTPStatusError (4xx/5xx):
    → log + return []
except Exception:
    → log + return []
    ↓
If [] returned → "No jobs found" message shown
```

---

## 8. Rate Limiting Strategy

| Limit Type | Limit | Our Handling |
|---|---|---|
| JSearch Free API | 200 req/month | Log usage; graceful "limit reached" msg |
| Telegram Bot API | 30 msg/sec | asyncio.sleep(0.4) between messages |
| Per-chat Telegram | 1 msg/sec | Handled by library |
| httpx Timeout | Custom 20s | TimeoutException caught |

---

## 9. Security Architecture

| Concern | Handling |
|---|---|
| Bot Token | Stored in `.env`, never in code |
| API Key | Stored in `.env`, never in code |
| User Data | No PII stored — only user_id and query |
| `.env` file | Add to `.gitignore` |
| HTTPS | All API calls over HTTPS by default |
