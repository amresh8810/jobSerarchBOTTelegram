# 03 — Information Architecture (IA)
## Telegram Job Search AI Agent

---

## 1. Overview

यह document define करता है कि bot की conversations कैसे flow करती हैं, commands कैसे organized हैं, और data किस structure में exist करता है।

---

## 2. Bot Command Map

```
Telegram Bot
│
├── /start          → Welcome message + feature overview
├── /help           → Detailed help guide
├── /search [query] → Direct job search with query
├── /trending       → Trending jobs in India today
└── /clear          → Clear user session + search history

[Plain Text Message]
└── Any text → Treated as job search query
```

---

## 3. Conversation Flow Map

### 3.1 New User Flow

```
User opens bot
      ↓
Sends /start
      ↓
Bot shows:
  • Welcome message (personalized)
  • What the bot does
  • How to search
  • Example queries
  • All commands list
      ↓
User types a search query
      ↓
[Search Flow begins]
```

---

### 3.2 Core Search Flow

```
User types: "Python Developer Mumbai"
      ↓
Bot: "🔍 Searching... ⏳"
      ↓
Query Enhancement:
  • "Python Developer Mumbai" → no change
  • "Python Developer" → "Python Developer India" (auto-add India)
      ↓
JSearch API Call
      ↓
  ┌──────────────────────────────────┐
  │        API Response              │
  └──────────────────────────────────┘
         ↓               ↓
    [Jobs Found]    [No Jobs Found]
         ↓               ↓
  Show Header       Show friendly
  "X jobs mile!"    "No results" msg
         ↓           + Suggestions
  Show Job Cards
  (1 per message, max 5)
         ↓
  [If > 5 results]
         ↓
  "Aur Jobs Dekho" button
         ↓
  User clicks → Jobs 6-8 shown
```

---

### 3.3 Job Card Structure

```
━━━━━━━━━━━━━━━━━━━━━━━━━
🔢 Job #1
━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️  [JOB TITLE]

🏢  Company: [COMPANY NAME] [RATING]
📍  Location: [CITY, STATE, COUNTRY or 🏠 Remote]
💼  Type: [Full-time / Part-time / Contract] • [Posted Date]
💰  Salary: [₹XL - ₹YL/year or "Not mentioned"]

📝  Description:
[First 300 characters of JD]...

[✅ Apply Now]  [🏢 Company]
[🔍 Naya Search]
```

---

### 3.4 Error Flow

```
API Timeout / Error
      ↓
Log error silently
      ↓
Show user: "⚠️ Kuch error aayi. /start karke dobara try karo."
      ↓
Bot continues working for other users

━━━━━━━━━━━━━━━━━━━━━━━━━

No Results Found
      ↓
Show: "😔 '[query]' ke liye jobs nahi mili."
      ↓
Show 3 suggestions:
  • Location add karo
  • Keywords change karo
  • Broader search try karo
```

---

## 4. User Session Architecture

```
user_sessions = {
    user_id (int): {
        "query": "Python Developer Mumbai",    # Last search
        "results": [job1, job2, ...],          # All fetched results
        "page": 0                              # Current page
    }
}
```

**Session Lifecycle:**
- Created: When user does first search
- Updated: On every new search
- Pagination: /page_1 shows jobs 6-10 from same session
- Cleared: via /clear command, or after 1 hour (future)
- Storage: In-memory dict (Python) — no database in MVP

---

## 5. Data Entity Structure

### 5.1 Job Object (Internal)

```python
job = {
    "title": "Senior Python Developer",
    "company": "TCS",
    "location": "Mumbai, Maharashtra, India",
    "salary": "₹12L - ₹18L/year",
    "description": "We are looking for...",
    "job_type": "Full-time",
    "apply_url": "https://jobs.lever.co/tcs/...",
    "company_url": "https://tcs.com",
    "rating": "",
    "posted": "2 din pehle",
    "skills": "Python, Django, REST APIs",
    "experience": "3+ years",
    "is_remote": False,
    "source": "LinkedIn"
}
```

### 5.2 Search Query Flow

```
User Input: "python developer mumbai"
      ↓
_enhance_query():
  • Strip whitespace
  • Check for location keywords
  • If no location → add "India"
      ↓
Enhanced Query: "python developer mumbai"
      ↓
JSearch API: query="python developer mumbai"
      ↓
Raw API Response (list of job dicts)
      ↓
_parse_job() for each job
      ↓
Clean Job Objects (list)
      ↓
format_job_card() for each
      ↓
Telegram Messages sent
```

---

## 6. Bot Navigation Map with Commands

```
User Chat
│
├── [Any Text] ─────────────────────→ job search → results
│
├── /start ──────────────────────────→ welcome screen
│
├── /help ───────────────────────────→ help guide
│
├── /search [role] [location] ───────→ job search → results
│
├── /trending ───────────────────────→ trending jobs (pre-set query)
│
├── /clear ──────────────────────────→ session cleared
│
└── [Inline Button: Apply Now] ──────→ opens job URL in browser
    [Inline Button: Company] ────────→ opens company website
    [Inline Button: Load More] ──────→ next page of results
    [Inline Button: Naya Search] ────→ prompts for new query
```

---

## 7. Content Taxonomy

### 7.1 Job Types
- `Full-time` (FULLTIME)
- `Part-time` (PARTTIME)
- `Contract` (CONTRACTOR)
- `Internship` (INTERN)
- `Temporary` (TEMPORARY)
- `Remote` (remote flag)

### 7.2 Job Sources
- LinkedIn
- Indeed
- Glassdoor
- ZipRecruiter
- Naukri
- Other Job Portals

### 7.3 Salary Formats (India)
- Lakhs per year: `₹8L - ₹12L/year`
- Thousands per month: `₹45K - ₹80K/month`
- Not available: `Not mentioned`

---

## 8. Notification Architecture (Phase 2)

```
Job Alert Subscription
      ↓
Scheduler (APScheduler / Cron)
Runs every day at 9:00 AM IST
      ↓
For each subscribed user:
  → fetch fresh jobs for their query
  → send top 5 as Telegram messages
  → log delivery status
```

---

## 9. Supported Languages (Search Queries)

| Language | Status | Notes |
|---|---|---|
| English | ✅ Supported | Primary language |
| Hindi (Romanized) | ⚠️ Partial | Auto-transliterated in results |
| Hindi (Devanagari) | ❌ Phase 2 | STT/translation needed |
| Hinglish | ✅ Works | Mixed English-Hindi queries work |
