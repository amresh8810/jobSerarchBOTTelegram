# 05 — Database Schema
## Telegram Job Search AI Agent

---

## 1. MVP: No Database (Stateless Design)

MVP version में **कोई database नहीं है**। सभी data in-memory (Python dict) में रहता है। Bot restart होने पर सभी sessions clear हो जाते हैं — यह MVP के लिए acceptable है।

### क्यों No Database in MVP?
- Bot stateless रहे → simpler deployment
- User search history privacy
- Zero infrastructure cost
- Faster development

---

## 2. In-Memory Data Structure (Current MVP)

```python
# ─── Active User Sessions ─────────────────────────────────────────
user_sessions: dict[int, dict] = {
    # key: Telegram user_id (int)
    # value: session dict
    
    987654321: {
        "query": "Data Scientist Bangalore",
        "results": [
            {
                "title": "Senior Data Scientist",
                "company": "Flipkart",
                "location": "Bangalore, Karnataka, India",
                "salary": "₹20L - ₹35L/year",
                "description": "Looking for a passionate DS...",
                "job_type": "Full-time",
                "apply_url": "https://...",
                "company_url": "https://flipkart.com",
                "rating": "",
                "posted": "3 din pehle",
                "skills": "Python, ML, TensorFlow",
                "experience": "4+ years",
                "is_remote": False,
                "source": "LinkedIn"
            },
            # ... more jobs
        ],
        "page": 0,
        "searched_at": "2026-02-28T22:10:00"
    }
}
```

---

## 3. Phase 2: SQLite Schema (Local Persistent Storage)

Phase 2 mein hum **SQLite** add karenge for:
- Search history
- Saved jobs
- Alert subscriptions
- Usage analytics

### Table: `users`
```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,      -- Telegram user_id
    first_name      TEXT,
    username        TEXT,
    language_code   TEXT DEFAULT 'en',
    joined_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active     DATETIME,
    total_searches  INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT 1
);
```

### Table: `searches`
```sql
CREATE TABLE searches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    query           TEXT NOT NULL,
    results_count   INTEGER DEFAULT 0,
    searched_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_searches_user ON searches(user_id);
CREATE INDEX idx_searches_query ON searches(query);
```

### Table: `saved_jobs`
```sql
CREATE TABLE saved_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    job_title       TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    salary          TEXT,
    apply_url       TEXT,
    source          TEXT,
    saved_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_applied      BOOLEAN DEFAULT 0,
    applied_at      DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_saved_user ON saved_jobs(user_id);
```

### Table: `job_alerts`
```sql
CREATE TABLE job_alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    query           TEXT NOT NULL,           -- e.g., "Python Developer Mumbai"
    frequency       TEXT DEFAULT 'daily',    -- daily | weekly
    send_time       TEXT DEFAULT '09:00',    -- HH:MM IST
    is_active       BOOLEAN DEFAULT 1,
    last_sent_at    DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Table: `analytics_events`
```sql
CREATE TABLE analytics_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    event_type      TEXT NOT NULL,   -- search | apply_click | load_more | error
    event_data      TEXT,            -- JSON string with event metadata
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_type ON analytics_events(event_type);
CREATE INDEX idx_events_date ON analytics_events(created_at);
```

---

## 4. Phase 3: PostgreSQL Schema (Production Scale)

Phase 3 mein production-grade database ke liye PostgreSQL.

### Enhanced `users` Table
```sql
CREATE TABLE users (
    id              BIGINT PRIMARY KEY,        -- Telegram user_id
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    username        VARCHAR(100),
    language_code   VARCHAR(10) DEFAULT 'en',
    phone_number    VARCHAR(20),               -- if bot has phone access
    is_premium      BOOLEAN DEFAULT FALSE,
    plan            VARCHAR(20) DEFAULT 'free', -- free | pro | enterprise
    joined_at       TIMESTAMPTZ DEFAULT NOW(),
    last_active     TIMESTAMPTZ,
    total_searches  INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    is_blocked      BOOLEAN DEFAULT FALSE
);
```

### Enhanced `searches` Table
```sql
CREATE TABLE searches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         BIGINT NOT NULL REFERENCES users(id),
    query           VARCHAR(500) NOT NULL,
    enhanced_query  VARCHAR(500),
    results_count   INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    api_source      VARCHAR(50) DEFAULT 'jsearch',
    searched_at     TIMESTAMPTZ DEFAULT NOW()
);
```

### `popular_queries` View
```sql
CREATE VIEW popular_queries AS
SELECT 
    LOWER(query) as query,
    COUNT(*) as search_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(results_count) as avg_results,
    DATE(searched_at) as date
FROM searches
GROUP BY LOWER(query), DATE(searched_at)
ORDER BY search_count DESC;
```

---

## 5. Local Cache (Redis — Phase 3)

Jobs ko cache karna (same query → same results for 30 minutes):

```
Key Pattern:    jobs:{md5(query)}
Value:          JSON array of job objects
TTL:            30 minutes
Max Memory:     256MB
Eviction:       allkeys-lru
```

```python
# Cache key example
import hashlib
cache_key = f"jobs:{hashlib.md5(query.encode()).hexdigest()}"
# → "jobs:a1b2c3d4e5f6..."
```

---

## 6. Data Retention Policy

| Data Type | MVP Retention | Phase 2 | Phase 3 |
|---|---|---|---|
| User sessions | Session only (in-memory) | 30 days | 90 days |
| Search queries | Not stored | 60 days | 1 year |
| Saved jobs | Not stored | User lifetime | User lifetime |
| Job alerts | Not stored | Until unsubscribed | Until unsubscribed |
| Analytics | Not stored | 90 days | 2 years |

---

## 7. Privacy Compliance

| Principle | Implementation |
|---|---|
| Data Minimization | Only user_id and query stored — no PII |
| Right to Delete | /deletedata command (Phase 2) |
| Transparency | Privacy note shown in /start |
| No PII in logs | Logs show user_id, not name/phone |
