# 08 — Scoring Engine Specification
## Telegram Job Search AI Agent

---

## 1. Overview

Scoring Engine bot के results की **quality और relevancy** measure करता है। यह ensure करता है कि user को सबसे relevant jobs पहले दिखें।

MVP में scoring basic है — Phase 2 में ML-based ranking आएगी।

---

## 2. Job Relevancy Score (MVP)

### 2.1 Purpose
जब multiple jobs return हों, तो सबसे relevant jobs पहले दिखाओ।

### 2.2 Scoring Formula (Rule-Based)

```
Relevancy_Score = (
    title_match_score × 0.35 +
    location_match_score × 0.25 +
    salary_available_score × 0.15 +
    recency_score × 0.15 +
    description_quality_score × 0.10
)
```

### 2.3 Individual Score Components

#### A) Title Match Score (0–10)

| Condition | Score |
|---|---|
| Query keyword exact match in title | 10 |
| Partial keyword match | 6 |
| Related role match | 4 |
| Weak/no match | 1 |

```python
def title_match_score(query: str, job_title: str) -> float:
    query_words = set(query.lower().split())
    title_words = set(job_title.lower().split())
    
    # Exact keyword match
    common = query_words & title_words
    if len(common) >= 2:
        return 10.0
    elif len(common) == 1:
        return 6.0
    
    # Partial match (substring)
    for word in query_words:
        if any(word in t for t in title_words):
            return 4.0
    
    return 1.0
```

---

#### B) Location Match Score (0–10)

| Condition | Score |
|---|---|
| Location exact match | 10 |
| Same state/region | 7 |
| Remote job (if remote in query) | 9 |
| Different city, same country | 4 |
| Different country | 1 |
| No location in query | 5 (neutral) |

---

#### C) Salary Available Score (0–10)

| Condition | Score |
|---|---|
| Salary range provided | 10 |
| Only min salary | 7 |
| Salary mentioned in highlights | 5 |
| "Not mentioned" | 0 |

---

#### D) Recency Score (0–10)

| Posted When | Score |
|---|---|
| Today | 10 |
| 1-3 days ago | 8 |
| 4-7 days ago | 6 |
| 1-2 weeks ago | 4 |
| 3-4 weeks ago | 2 |
| Older / Unknown | 1 |

```python
def recency_score(posted_at: str) -> float:
    if not posted_at:
        return 1.0
    from datetime import datetime, timezone
    posted = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    days_old = (datetime.now(timezone.utc) - posted).days
    if days_old == 0: return 10.0
    elif days_old <= 3: return 8.0
    elif days_old <= 7: return 6.0
    elif days_old <= 14: return 4.0
    elif days_old <= 30: return 2.0
    else: return 1.0
```

---

#### E) Description Quality Score (0–10)

| Condition | Score |
|---|---|
| Description > 200 chars with responsibilities | 10 |
| Description > 100 chars | 7 |
| Description < 100 chars | 4 |
| No description | 0 |

---

### 2.4 Final Sort

```python
def rank_jobs(jobs: list[dict], query: str) -> list[dict]:
    """Sort jobs by relevancy score, highest first."""
    scored_jobs = []
    for job in jobs:
        score = calculate_relevancy(job, query)
        scored_jobs.append((score, job))
    
    scored_jobs.sort(key=lambda x: x[0], reverse=True)
    return [job for _, job in scored_jobs]
```

---

## 3. Query Quality Score

### 3.1 Purpose
Detect if user's query is good enough for a useful search.

### 3.2 Query Scoring Rules

| Check | Score | Action if Fail |
|---|---|---|
| Length ≥ 3 chars | +20 | Ask for more detail |
| Contains role keyword | +30 | Suggest adding role |
| Contains location | +20 | Auto-add "India" |
| Not a question | +15 | Treat as search |
| Not gibberish | +15 | Ask to rephrase |

```python
def score_query(query: str) -> dict:
    score = 0
    issues = []
    
    if len(query) >= 3:
        score += 20
    else:
        issues.append("Query too short")
    
    role_keywords = ["developer", "engineer", "manager", "analyst", 
                     "designer", "consultant", "intern", "executive"]
    if any(kw in query.lower() for kw in role_keywords):
        score += 30
    else:
        issues.append("No role keyword detected")
    
    location_keywords = ["mumbai", "delhi", "bangalore", "india", "remote"]
    if any(loc in query.lower() for loc in location_keywords):
        score += 20
    
    return {
        "score": score,
        "quality": "good" if score >= 50 else "fair" if score >= 30 else "poor",
        "issues": issues
    }
```

---

## 4. Result Quality Metrics

### 4.1 Search Session Metrics

Har search session ke baad internally track karo (Phase 2):

| Metric | Calculation | Target |
|---|---|---|
| Result Count | len(jobs) returned | ≥ 3 |
| Avg Salary Coverage | jobs_with_salary / total_jobs | ≥ 50% |
| Avg Recency | avg days_old of results | ≤ 14 days |
| Apply URL Coverage | jobs_with_apply_url / total | ≥ 80% |

---

## 5. Trending Jobs Algorithm

### 5.1 How "Trending" is Calculated (Phase 2)

MVP mein pre-defined query hai. Phase 2 mein actual trending based on:

```python
# Trending = Most searched in last 24 hours
# (from SQLite search_queries table)

SELECT 
    LOWER(query) as query,
    COUNT(*) as search_count
FROM searches
WHERE searched_at > datetime('now', '-24 hours')
GROUP BY LOWER(query)
ORDER BY search_count DESC
LIMIT 5;
```

---

## 6. Anti-Spam Scoring (Phase 2)

Rate limiting per user:

| Limit | Action |
|---|---|
| > 10 searches in 1 minute | 60-second cooldown |
| > 50 searches in 1 hour | 1-hour cooldown |
| > 200 searches in 1 day | 24-hour cooldown |
| Repeated same query 5x | Suggest changing query |

```python
def is_rate_limited(user_id: int, search_times: list) -> tuple[bool, str]:
    now = datetime.now()
    recent_1min = [t for t in search_times if (now - t).seconds < 60]
    
    if len(recent_1min) > 10:
        return True, "60 second baad try karo 🕐"
    return False, ""
```

---

## 7. Search Result Diversity Score

Same company se multiple jobs hide karo:

```python
def deduplicate_by_company(jobs: list[dict], max_per_company: int = 2) -> list[dict]:
    """Ensure no more than max_per_company from same employer."""
    company_counts = {}
    result = []
    
    for job in jobs:
        company = job["company"].lower()
        if company_counts.get(company, 0) < max_per_company:
            result.append(job)
            company_counts[company] = company_counts.get(company, 0) + 1
    
    return result
```

---

## 8. Salary Normalization

Different salary formats ko comparable banao:

```python
def normalize_salary_to_annual_inr(
    min_sal: float,
    max_sal: float,
    period: str,
    currency: str
) -> tuple[float, float]:
    """Normalize all salaries to Annual INR for comparison."""
    
    USD_TO_INR = 83.5
    
    # Period multipliers
    multipliers = {
        "YEAR": 1,
        "MONTH": 12,
        "HOUR": 2080,    # 40hrs/week × 52 weeks
        "DAY": 260        # 5 days/week × 52 weeks
    }
    mult = multipliers.get(period, 1)
    
    # Currency conversion
    if currency == "USD":
        min_inr = min_sal * mult * USD_TO_INR
        max_inr = max_sal * mult * USD_TO_INR
    else:  # Already INR
        min_inr = min_sal * mult
        max_inr = max_sal * mult
    
    return min_inr, max_inr
```
