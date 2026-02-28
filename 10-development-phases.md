# 10 — Development Phases
## Telegram Job Search AI Agent

---

## 1. Overview

```
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   PHASE 1      │  │   PHASE 2      │  │   PHASE 3      │
│   MVP          │  │   Growth       │  │   Scale        │
│   Week 1-2     │  │   Week 3-6     │  │   Week 7-12    │
│   ✅ DONE      │  │   🔧 Upcoming  │  │   📋 Planned   │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## 2. Phase 1 — MVP (Week 1-2) ✅

### Goal
Working Telegram bot जो internet से jobs search करके Telegram में show करे।

### Sprint 1 (Day 1-3): Core Setup

| Task | Time Estimate | Status |
|---|---|---|
| Telegram bot create via BotFather | 15 min | ✅ Done |
| RapidAPI account + JSearch subscribe | 15 min | ✅ Done |
| Python environment setup | 30 min | ✅ Done |
| `requirements.txt` create | 10 min | ✅ Done |
| `.env` file structure | 10 min | ✅ Done |
| Basic `bot.py` skeleton | 2 hours | ✅ Done |
| `/start` and `/help` commands | 1 hour | ✅ Done |

---

### Sprint 2 (Day 4-7): Job Search Integration

| Task | Time Estimate | Status |
|---|---|---|
| `job_searcher.py` — base class | 2 hours | ✅ Done |
| JSearch API integration | 3 hours | ✅ Done |
| `search_jobs()` method | 2 hours | ✅ Done |
| `_parse_job()` — field extraction | 2 hours | ✅ Done |
| `_parse_salary()` — INR/USD format | 1 hour | ✅ Done |
| `_clean_description()` | 1 hour | ✅ Done |
| Error handling (timeout, 429, 422) | 2 hours | ✅ Done |

---

### Sprint 3 (Day 8-10): UI & UX

| Task | Time Estimate | Status |
|---|---|---|
| `format_job_card()` Markdown format | 2 hours | ✅ Done |
| `build_job_keyboard()` inline buttons | 1 hour | ✅ Done |
| `perform_search()` orchestrator | 2 hours | ✅ Done |
| Pagination (Load More button) | 1 hour | ✅ Done |
| `/trending` command | 1 hour | ✅ Done |
| `/search` command with args | 30 min | ✅ Done |
| `/clear` session command | 30 min | ✅ Done |
| Plain text fallback | 1 hour | ✅ Done |
| `README.md` documentation | 2 hours | ✅ Done |

**MVP Deliverable**: ✅ Working bot — type job query → get results

---

## 3. Phase 2 — Growth (Week 3-6)

### Goal
Better results, persistence, user retention features.

### Feature 2.1: Smart Query Enhancement (Week 3)

| Task | Details |
|---|---|
| Salary filter parsing | "above 10 lakh" → API filter |
| Job type detection | "remote", "intern", "part-time" in query |
| Experience level detect | "fresher", "senior", "5 years" |
| City normalization | "blore" → "Bangalore" |
| Spell correction (basic) | "enginer" → "engineer" |

**Code change: `_enhance_query()` in `job_searcher.py`**

---

### Feature 2.2: Job Alerts / Subscriptions (Week 3-4)

| Task | Details |
|---|---|
| `/subscribe [query]` command | Save user's query |
| SQLite database integration | `aiosqlite` library |
| `alert_scheduler.py` | APScheduler: send daily at 9 AM |
| `/unsubscribe` command | Remove alert |
| `/myalerts` command | List active subscriptions |
| Max 3 alerts per user | Rate limit |

---

### Feature 2.3: Save Jobs (Week 4)

| Task | Details |
|---|---|
| `💾 Save Job` button on each card | SQLite storage |
| `/saved` command | View saved jobs list |
| `/unsave [id]` command | Remove saved job |
| `/applied [id]` command | Mark job as applied |
| Max 20 saved jobs per user | Limit with warning |

---

### Feature 2.4: Search History (Week 5)

| Task | Details |
|---|---|
| `/history` command | Last 10 searches |
| Repeat search from history | Button on each history item |
| `/clearhistory` command | Delete all history |

---

### Feature 2.5: Hindi Support (Week 5-6)

| Task | Details |
|---|---|
| Devanagari input detection | Check Unicode range |
| Google Translate API integration | Hindi query → English |
| Response still in English | (Translation of results = Phase 3) |
| Hybrid message (Hindi + English) | Mix both |

---

### Feature 2.6: Performance (Week 6)

| Task | Details |
|---|---|
| Redis caching (optional) | Same query → cached result for 30 min |
| Connection pooling | httpx AsyncClient reuse |
| Rate limiting per user | 10 searches/minute max |
| Webhook mode deployment | Faster than long polling |

---

## 4. Phase 3 — Scale (Week 7-12)

### Goal
Production-grade, multi-user, monetizable platform.

### Feature 3.1: Resume Matching (Week 7-8)

| Task | Details |
|---|---|
| `/resume` upload command | Accept PDF file |
| PDF text extraction | PyPDF2 / pdfplumber |
| Skills extraction from resume | Regex + NLP |
| Matched job suggestions | Skills → search query auto-generated |

---

### Feature 3.2: Premium Plan (Week 9-10)

| Tier | Price | Features |
|---|---|---|
| Free | ₹0/month | 200 searches + 3 alerts |
| Pro | ₹199/month | Unlimited searches + 10 alerts + Resume matching |
| Teams | ₹499/month | 5 users + analytics dashboard |

| Task | Details |
|---|---|
| Razorpay payment integration | UPI + Card payments |
| `/premium` command | Upgrade flow |
| `/plan` command | Current plan info |
| Feature gate per plan | Check plan before premium features |

---

### Feature 3.3: Web Dashboard (Week 11-12)

```
Admin Dashboard (FastAPI + simple HTML):
- Total users
- Searches per day graph
- Most popular queries
- Revenue metrics
- Error rate monitoring
```

---

### Feature 3.4: Multi-Platform (Week 12)

| Platform | Priority | Status |
|---|---|---|
| Telegram | ✅ Phase 1 | Done |
| WhatsApp | 🔧 Phase 3 | Meta Business API |
| Slack Bot | 📋 Phase 3 | Slack API |
| Discord Bot | 📋 Phase 3 | Discord.py |

---

## 5. Milestone Summary

| Milestone | Target | Deliverable |
|---|---|---|
| **M1: MVP Live** | Day 10 | Working Telegram bot |
| M2: Alerts Live | Week 4 | Daily job alert subscriptions |
| M3: Save Feature | Week 4 | Saved jobs + applied tracking |
| M4: Hindi Support | Week 6 | Hindi query support |
| M5: Webhook Deploy | Week 6 | Production VPS deployment |
| M6: Resume Match | Week 8 | PDF resume upload + job match |
| M7: Premium Launch | Week 10 | Paid tier with Razorpay |
| M8: Dashboard | Week 12 | Admin analytics web dashboard |
| M9: WhatsApp | Week 14+ | WhatsApp bot (same logic) |

---

## 6. Release Strategy

```
Feature Dev (local) 
        ↓
Manual Testing (Telegram real phone)
        ↓
Update README / docs
        ↓
Deploy to VPS (Phase 2+)
        ↓
Monitor for 24 hours
        ↓
Announce to users (broadcast message)
```

---

## 7. Versioning

| Version | Features |
|---|---|
| v1.0 | MVP — basic job search |
| v1.1 | UI improvements, better salary format |
| v1.2 | Query enhancement (salary filter, remote) |
| v2.0 | Alerts + Saved Jobs + SQLite |
| v2.5 | Hindi support + performance |
| v3.0 | Resume matching + Premium |
