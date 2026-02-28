# 09 — Engineering Scope Definition
## Telegram Job Search AI Agent

---

## 1. Purpose

यह document clearly define करता है कि **क्या build होगा** (in-scope), **क्या नहीं** (out-of-scope), **team structure**, और **technical decisions** — ताकि development focus रहे।

---

## 2. MVP In-Scope Features

### S-01: Telegram Bot Core

| Item | Details | Status |
|---|---|---|
| Bot setup via BotFather | Token-based auth | ✅ Done |
| Long polling mode | No server needed for MVP | ✅ Done |
| `/start` command | Welcome + intro message | ✅ Done |
| `/help` command | Full usage guide | ✅ Done |
| `/search` command | Args-based search | ✅ Done |
| `/trending` command | Pre-defined popular query | ✅ Done |
| `/clear` command | Session reset | ✅ Done |
| Plain text handler | Any text → job search | ✅ Done |
| Inline buttons | Apply, Company, Load More | ✅ Done |
| Callback handler | Button press handling | ✅ Done |
| Error handler | Global exception catch | ✅ Done |
| Typing indicator | `ChatAction.TYPING` | ✅ Done |

---

### S-02: Job Search Engine

| Item | Details | Status |
|---|---|---|
| JSearch API integration | httpx async client | ✅ Done |
| Query enhancement | Auto-add "India" if no location | ✅ Done |
| Job parsing | Title, company, location, salary, description | ✅ Done |
| Salary formatting | ₹8L - ₹12L, Not mentioned | ✅ Done |
| INR/USD conversion display | Format numbers properly | ✅ Done |
| Description cleaning | Strip HTML, limit 400 chars | ✅ Done |
| Posted date formatting | "2 din pehle" style | ✅ Done |
| Remote job detection | Label as "🏠 Remote" | ✅ Done |
| Source detection | LinkedIn/Indeed/Glassdoor | ✅ Done |
| Error handling | Timeout, 429, 422 handled | ✅ Done |

---

### S-03: Display & UX

| Item | Details | Status |
|---|---|---|
| Job card format | Markdown with emoji | ✅ Done |
| Numbered cards | #1, #2, #3... | ✅ Done |
| Pagination | First 5 → Load More → 6-8 | ✅ Done |
| Session state | In-memory dict | ✅ Done |
| Plain text fallback | If Markdown fails | ✅ Done |

---

## 3. Out of Scope (MVP)

| Feature | Reason | Target |
|---|---|---|
| Resume upload & matching | Complexity, file handling | Phase 2 |
| Job alerts / subscriptions | Needs scheduler + DB | Phase 2 |
| Saved jobs / wishlist | Needs DB | Phase 2 |
| Salary filter | API limitation | Phase 2 |
| Job type filter | API query enhancement | Phase 2 |
| Hindi language support | Translation layer needed | Phase 2 |
| Company reviews | Separate API needed | Phase 2 |
| Interview tips | Content curation needed | Phase 3 |
| Multiple platform accounts | Single Telegram only | Phase 3 |
| WhatsApp integration | Meta Business API approval | Phase 3 |
| Web dashboard for admins | Out of scope for bot | Phase 3 |
| Payment / Premium plan | Monetization | Phase 3 |
| CI/CD pipeline | Not needed for single-file bot | Phase 2 |
| Docker containerization | Optional for productionl | Phase 2 |

---

## 4. Team Structure

### MVP Development (Solo / Small Team)

| Role | Person | Responsibility |
|---|---|---|
| **Developer** | 1 person | bot.py + job_searcher.py |
| **Tester** | Same person | Manual Telegram testing |
| **DevOps** | Same person | Run bot on local / VPS |
| **PM** | Same person | Feature prioritization |

### Phase 2 Team (Recommended)

| Role | Headcount |
|---|---|
| Backend Developer | 1 |
| DevOps | 0.5 (part-time) |
| QA | 0.5 (part-time) |
| Product Manager | 0.5 (part-time) |

---

## 5. Technical Decisions (ADRs)

### ADR-01: Language — Python
**Decision**: Python 3.10+  
**Reason**: Best ecosystem for Telegram bots (python-telegram-bot), async support, rapid development  
**Rejected**: Node.js (team prefers Python), Golang (overkill for MVP)

---

### ADR-02: Bot Mode — Long Polling vs Webhook
**Decision**: Long Polling for MVP  
**Reason**: Works without a public HTTPS server; no deployment complexity  
**Future**: Webhook mode in Phase 2 when deploying to VPS/Cloud  
**Rejected**: Webhook MVP (needs SSL cert, reverse proxy, domain)

---

### ADR-03: Job Search API — JSearch (RapidAPI)
**Decision**: JSearch API on RapidAPI  
**Reason**: Aggregates 10+ job platforms; simple REST API; free tier for testing  
**Rejected**: Scrapy (ToS violations), SerpAPI (costlier), LinkedIn Direct API (restricted)

---

### ADR-04: HTTP Client — httpx
**Decision**: httpx with async support  
**Reason**: Modern async HTTP client; better than requests for async bot  
**Rejected**: requests (synchronous, blocks event loop), aiohttp (more verbose)

---

### ADR-05: Storage — In-Memory Dict (MVP)
**Decision**: Python dict for session storage  
**Reason**: Zero configuration; sessions lost on restart (acceptable MVP behavior)  
**Future Phase 2**: SQLite (aiosqlite) for persistence  
**Future Phase 3**: PostgreSQL for scale  
**Rejected**: Redis MVP (overkill), SQLite MVP (premature optimization)

---

### ADR-06: Config — python-dotenv
**Decision**: .env file + python-dotenv  
**Reason**: Industry standard 12-factor app config; prevents key commit  
**Alternative**: AWS Secrets Manager (Phase 3 for production)

---

## 6. Engineering Standards

### 6.1 Code Style
```
- PEP 8 compliance
- Type hints for all function signatures
- Docstrings for all public functions
- Max line length: 100 characters
- Async functions for all I/O operations
```

### 6.2 Error Handling Rules
```
- All external API calls in try/except
- Never let exceptions crash the bot
- Always show user-friendly message on failure
- Log full traceback internally (not shown to user)
- Gracefully handle empty API responses
```

### 6.3 Naming Conventions
```python
# Functions: snake_case
async def perform_search():

# Constants: UPPER_CASE
JSEARCH_BASE_URL = "https://..."

# Classes: PascalCase
class JobSearcher:

# Private methods: _prefix
def _parse_job():
```

---

## 7. Definition of Ready (DoR)

Before picking up any new feature:
1. ✅ User story written with acceptance criteria
2. ✅ API contract (if external API involved) documented
3. ✅ Edge cases listed (empty results, API error, long input)
4. ✅ Testing approach defined

---

## 8. Definition of Done (DoD)

A feature is DONE when:
1. ✅ Code written
2. ✅ Manually tested in Telegram (real phone)
3. ✅ Error cases handled (no results, API failure)
4. ✅ No bot crashes on any input
5. ✅ Response time ≤ 5 seconds
6. ✅ README updated if feature changes user flow

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| JSearch free limit (200/month) | High | Medium | Upgrade to paid or cache results |
| RapidAPI service downtime | Low | High | Retry logic + friendly message |
| Telegram API outage | Very Low | High | Nothing to do; inform user |
| Bot token leaked (committed to git) | Medium | Critical | .gitignore .env; rotate token immediately |
| httpx version conflict | Low | Medium | Use compatible version ranges |
| Markdown parsing errors | Medium | Low | Plain text fallback already implemented |
| High query volume slows responses | Low | Medium | asyncio.sleep rate limiting |
