# 06 — API Contracts
## Telegram Job Search AI Agent

---

## 1. External APIs Used

इस bot में **2 external APIs** use होती हैं:
1. **Telegram Bot API** — bot को messages receive/send करने के लिए
2. **JSearch API (RapidAPI)** — internet se jobs search करने के लिए

---

## 2. JSearch API — Job Search

### Base URL
```
https://jsearch.p.rapidapi.com
```

### Authentication
```
Headers:
  X-RapidAPI-Key: {RAPIDAPI_KEY}
  X-RapidAPI-Host: jsearch.p.rapidapi.com
```

---

### 2.1 Search Jobs

**`GET /search`**

Job search करो across LinkedIn, Indeed, Glassdoor, etc.

**Request:**
```http
GET https://jsearch.p.rapidapi.com/search?query=Python+Developer+Mumbai&page=1&num_pages=1
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | ✅ | Job search query |
| `page` | string | ❌ | Page number (default: "1") |
| `num_pages` | string | ❌ | Pages to fetch (default: "1") |
| `date_posted` | string | ❌ | `all`, `today`, `3days`, `week`, `month` |
| `remote_jobs_only` | boolean | ❌ | Only remote jobs |
| `employment_types` | string | ❌ | `FULLTIME`, `PARTTIME`, `INTERN` |

**Response 200 (Success):**
```json
{
    "status": "OK",
    "request_id": "req-abc123",
    "parameters": {
        "query": "Python Developer Mumbai",
        "page": 1,
        "num_pages": 1
    },
    "data": [
        {
            "job_id": "abc123xyz",
            "employer_name": "TCS",
            "employer_logo": "https://...",
            "employer_website": "https://tcs.com",
            "employer_company_type": null,
            "job_publisher": "LinkedIn",
            "job_id": "...",
            "job_employment_type": "FULLTIME",
            "job_title": "Senior Python Developer",
            "job_apply_link": "https://www.linkedin.com/jobs/view/...",
            "job_apply_is_direct": false,
            "job_apply_quality_score": 0.8,
            "job_description": "We are looking for a Python Developer...",
            "job_is_remote": false,
            "job_posted_at_timestamp": 1709123456,
            "job_posted_at_datetime_utc": "2026-02-25T10:00:00Z",
            "job_city": "Mumbai",
            "job_state": "Maharashtra",
            "job_country": "IN",
            "job_latitude": 19.0760,
            "job_longitude": 72.8777,
            "job_benefits": null,
            "job_google_link": "https://www.google.com/search?q=...",
            "job_offer_expiration_datetime_utc": null,
            "job_required_experience": {
                "no_experience_required": false,
                "required_experience_in_months": 36,
                "experience_mentioned": true
            },
            "job_required_skills": ["Python", "Django", "REST APIs", "Docker"],
            "job_required_education": {
                "postgraduate_degree": false,
                "professional_certification": false,
                "high_school": false,
                "associates_degree": false,
                "bachelors_degree": true
            },
            "job_experience_in_place_of_education": false,
            "job_min_salary": 1200000,
            "job_max_salary": 1800000,
            "job_salary_currency": "INR",
            "job_salary_period": "YEAR",
            "job_highlights": {
                "Qualifications": ["3+ years Python experience"],
                "Responsibilities": ["Design and implement features"],
                "Benefits": ["Health insurance", "Remote work"]
            }
        }
    ]
}
```

**Response 422 (No Results):**
```json
{
    "status": "OK",
    "data": []
}
```

**Response 429 (Rate Limited):**
```json
{
    "message": "You have exceeded the MONTHLY quota"
}
```

---

### 2.2 Our Usage of JSearch Response

हम response से यह fields निकालते हैं:

| Our Field | JSearch Source Field |
|---|---|
| `title` | `job_title` |
| `company` | `employer_name` |
| `location` | `job_city` + `job_state` + `job_country` |
| `is_remote` | `job_is_remote` |
| `salary` | `job_min_salary` + `job_max_salary` + `job_salary_currency` |
| `description` | `job_description` (cleaned) |
| `job_type` | `job_employment_type` (mapped) |
| `apply_url` | `job_apply_link` or `job_google_link` |
| `company_url` | `employer_website` |
| `posted` | `job_posted_at_datetime_utc` (formatted) |
| `skills` | `job_required_skills` (first 5) |
| `experience` | `job_required_experience.required_experience_in_months` |
| `source` | `job_publisher` |

---

## 3. Telegram Bot API

### Base URL
```
https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/
```

> **Note:** हम directly API call नहीं करते — `python-telegram-bot` library use करते हैं जो इसे abstract करती है।

---

### 3.1 Methods Used (via Library)

#### `send_message`
Text message send karo.

```python
await update.message.reply_text(
    text="Hello! 👋",
    parse_mode=ParseMode.MARKDOWN
)
```

**Equivalent Raw API:**
```http
POST https://api.telegram.org/bot{TOKEN}/sendMessage
Content-Type: application/json

{
    "chat_id": 123456789,
    "text": "Hello! 👋",
    "parse_mode": "Markdown"
}
```

---

#### `send_message` with Inline Keyboard

```python
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Apply Now", url="https://job-url.com"),
        InlineKeyboardButton("🏢 Company", url="https://company.com")
    ],
    [InlineKeyboardButton("🔍 Naya Search", callback_data="new_search")]
])

await update.message.reply_text(
    text=job_card_text,
    parse_mode=ParseMode.MARKDOWN,
    reply_markup=keyboard
)
```

---

#### `edit_message_text`
Existing message edit karo (e.g., "Searching..." → delete).

```python
msg = await update.message.reply_text("⏳ Searching...")
# ... do search ...
await msg.delete()
```

---

#### `send_chat_action`
"Typing..." indicator show karo.

```python
await context.bot.send_chat_action(
    chat_id=update.effective_chat.id,
    action=ChatAction.TYPING
)
```

---

### 3.2 Webhook vs Long Polling

| Method | Description | When to Use |
|---|---|---|
| **Long Polling** (MVP) | Bot repeatedly asks Telegram for updates | Local dev, simple deployment |
| **Webhook** (Production) | Telegram sends updates to your URL | Production, VPS, Cloud |

**MVP (Long Polling Setup):**
```python
app.run_polling(allowed_updates=Update.ALL_TYPES)
```

**Production (Webhook Setup):**
```python
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    secret_token="YOUR_WEBHOOK_SECRET",
    webhook_url="https://yourdomain.com/webhook"
)
```

---

## 4. Internal Function Contracts

### `JobSearcher.search_jobs()`

```python
async def search_jobs(
    query: str,        # User's search query
    num_results: int = 8  # Max results to return
) -> list[dict]:
    """
    Returns: List of job dicts with these fields:
        title, company, location, salary, description,
        job_type, apply_url, company_url, rating,
        posted, skills, experience, is_remote, source
    
    Returns [] if:
        - API is unreachable
        - Timeout occurs (> 20s)
        - No results found
        - HTTP error (4xx/5xx)
    """
```

### `format_job_card()`

```python
def format_job_card(
    job: dict,    # Parsed job dict
    index: int    # Job number (1, 2, 3...)
) -> str:
    """
    Returns: Telegram Markdown-formatted string
    
    Format example:
    ━━━━━━━━━━━━━━━━━━━━━━━━━
    🔢 Job #1
    ━━━━━━━━━━━━━━━━━━━━━━━━━
    🏷️ *Senior Python Developer*
    
    🏢 *Company:* TCS
    📍 *Location:* Mumbai, Maharashtra, India
    💼 *Type:* Full-time • 3 din pehle
    💰 *Salary:* ₹12L - ₹18L/year
    
    📝 *Description:*
    We are looking for...
    """
```

### `build_job_keyboard()`

```python
def build_job_keyboard(job: dict) -> InlineKeyboardMarkup:
    """
    Returns keyboard with:
    Row 1: [Apply Now] [Company]  (only if URLs available)
    Row 2: [🔍 Naya Search]       (always present)
    """
```

---

## 5. Error Response Contracts

| Scenario | User Message | Log Level |
|---|---|---|
| No results | "😔 Jobs nahi mili. Try: add location, change keywords" | INFO |
| API timeout | "⚠️ Search time out. Dobara try karo." | WARNING |
| HTTP 429 (rate limit) | "😔 Abhi search nahi ho sakti. Thodi der baad try karo." | ERROR |
| HTTP 422 | "❌ Kuch gadbad hui. /start karke retry karo." | ERROR |
| Query too short | "🔍 Thoda detail mein likho, jaise: Python Developer Mumbai" | INFO |
| Bot crash | "⚠️ Kuch error aayi. Please /start karke dobara try karo." | CRITICAL |

---

## 6. Rate Limits Summary

| API | Limit | Our Handling |
|---|---|---|
| JSearch Free | 200 req/month | Graceful error + log |
| JSearch Basic ($10/mo) | 50 req/day | Production recommended |
| Telegram sendMessage | 30/sec global, 1/sec per chat | asyncio.sleep(0.4) |
| httpx timeout | 20 seconds | TimeoutException caught |
