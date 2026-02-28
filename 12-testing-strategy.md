# 12 — Testing Strategy
## Telegram Job Search AI Agent

---

## 1. Testing Philosophy

Telegram bot के लिए testing थोड़ी अलग है — कोई website नहीं, कोई browser नहीं। हम यह approaches use करते हैं:

```
         ┌──────────────────────┐
         │    Manual Testing    │  ← Real Telegram phone testing
         │    (Telegram)        │
         ├──────────────────────┤
         │   Unit Tests         │  ← pytest (Python functions)
         │   (pytest)           │
         ├──────────────────────┤
         │   API Mock Tests     │  ← Mock JSearch API responses
         │   (respx / httpx)   │
         └──────────────────────┘
```

---

## 2. Test Categories

### 2.1 Unit Tests — `job_searcher.py`

**Tool**: `pytest` + `pytest-asyncio`  
**Coverage Target**: ≥ 80%  

```python
# tests/test_job_searcher.py

import pytest
from job_searcher import JobSearcher

# ─── Test: _enhance_query() ──────────────────────────────────────

class TestEnhanceQuery:
    
    def test_adds_india_when_no_location(self):
        searcher = JobSearcher(api_key="dummy")
        result = searcher._enhance_query("Python Developer")
        assert "India" in result or "india" in result.lower()
    
    def test_does_not_add_india_when_location_present(self):
        searcher = JobSearcher(api_key="dummy")
        result = searcher._enhance_query("Python Developer Mumbai")
        # Should not add India (Mumbai is already there)
        assert result.count("India") <= 1
    
    def test_strips_whitespace(self):
        searcher = JobSearcher(api_key="dummy")
        result = searcher._enhance_query("  Python Developer  ")
        assert result.startswith("Python")
    
    def test_remote_keyword_preserved(self):
        searcher = JobSearcher(api_key="dummy")
        result = searcher._enhance_query("Data Scientist remote")
        assert "remote" in result.lower()


# ─── Test: _parse_salary() ───────────────────────────────────────

class TestParseSalary:
    
    def setup_method(self):
        self.searcher = JobSearcher(api_key="dummy")
    
    def test_inr_salary_range(self):
        raw = {
            "job_min_salary": 1200000,
            "job_max_salary": 1800000,
            "job_salary_currency": "INR",
            "job_salary_period": "YEAR",
            "job_highlights": {}
        }
        result = self.searcher._parse_salary(raw)
        assert "₹" in result
        assert "12L" in result
        assert "18L" in result
    
    def test_usd_salary(self):
        raw = {
            "job_min_salary": 80000,
            "job_max_salary": 120000,
            "job_salary_currency": "USD",
            "job_salary_period": "YEAR",
            "job_highlights": {}
        }
        result = self.searcher._parse_salary(raw)
        assert "$" in result
        assert "80K" in result
    
    def test_no_salary_returns_not_mentioned(self):
        raw = {
            "job_min_salary": None,
            "job_max_salary": None,
            "job_salary_currency": "INR",
            "job_salary_period": None,
            "job_highlights": {}
        }
        result = self.searcher._parse_salary(raw)
        assert result == "Not mentioned"


# ─── Test: _clean_description() ──────────────────────────────────

class TestCleanDescription:
    
    def setup_method(self):
        self.searcher = JobSearcher(api_key="dummy")
    
    def test_removes_html_tags(self):
        raw_text = "<p>We are looking for a <strong>developer</strong></p>"
        result = self.searcher._clean_description(raw_text)
        assert "<" not in result
        assert ">" not in result
    
    def test_truncates_long_description(self):
        long_text = "a" * 1000
        result = self.searcher._clean_description(long_text)
        assert len(result) <= 410  # 400 chars + some tolerance
    
    def test_empty_returns_default_message(self):
        result = self.searcher._clean_description("")
        assert result == "Description not available"
    
    def test_removes_markdown_special_chars(self):
        text = "We need *Python* developer with `REST` API skills"
        result = self.searcher._clean_description(text)
        assert "*" not in result
        assert "`" not in result


# ─── Test: _format_posted_date() ─────────────────────────────────

class TestFormatPostedDate:
    
    def setup_method(self):
        self.searcher = JobSearcher(api_key="dummy")
    
    def test_today_returns_aaj(self):
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).isoformat()
        result = self.searcher._format_posted_date(today)
        assert "Aaj" in result or "aaj" in result.lower()
    
    def test_empty_date_returns_empty(self):
        result = self.searcher._format_posted_date("")
        assert result == ""
    
    def test_invalid_date_returns_empty(self):
        result = self.searcher._format_posted_date("not-a-date")
        assert result == ""


# ─── Test: _format_number() ──────────────────────────────────────

class TestFormatNumber:
    
    def setup_method(self):
        self.searcher = JobSearcher(api_key="dummy")
    
    def test_inr_lakh_format(self):
        result = self.searcher._format_number(1500000, "INR")
        assert result == "15.0L"
    
    def test_inr_thousands(self):
        result = self.searcher._format_number(80000, "INR")
        assert result == "80K"
    
    def test_usd_millions(self):
        result = self.searcher._format_number(1500000, "USD")
        assert result == "1.5M"
    
    def test_usd_thousands(self):
        result = self.searcher._format_number(80000, "USD")
        assert result == "80K"
```

---

### 2.2 Integration Tests — JSearch API Mock

```python
# tests/test_api_integration.py

import pytest
import respx
import httpx
from job_searcher import JobSearcher

# Sample mock API response
MOCK_JOB_RESPONSE = {
    "status": "OK",
    "data": [
        {
            "job_title": "Senior Python Developer",
            "employer_name": "TCS",
            "employer_website": "https://tcs.com",
            "job_employment_type": "FULLTIME",
            "job_apply_link": "https://tcs.com/apply",
            "job_description": "We are looking for Python developer...",
            "job_is_remote": False,
            "job_posted_at_datetime_utc": "2026-02-26T10:00:00Z",
            "job_city": "Mumbai",
            "job_state": "Maharashtra",
            "job_country": "IN",
            "job_min_salary": 1200000,
            "job_max_salary": 1800000,
            "job_salary_currency": "INR",
            "job_salary_period": "YEAR",
            "job_required_skills": ["Python", "Django"],
            "job_required_experience": {"required_experience_in_months": 36},
            "job_publisher": "LinkedIn",
            "job_highlights": {}
        }
    ]
}

@pytest.mark.asyncio
@respx.mock
async def test_search_jobs_success():
    """Test successful job search with mocked API."""
    respx.get("https://jsearch.p.rapidapi.com/search").mock(
        return_value=httpx.Response(200, json=MOCK_JOB_RESPONSE)
    )
    
    searcher = JobSearcher(api_key="test-key")
    jobs = await searcher.search_jobs("Python Developer Mumbai")
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Senior Python Developer"
    assert jobs[0]["company"] == "TCS"
    assert "₹" in jobs[0]["salary"]
    assert jobs[0]["job_type"] == "Full-time"


@pytest.mark.asyncio
@respx.mock
async def test_search_jobs_empty_results():
    """Test handling when API returns no results."""
    respx.get("https://jsearch.p.rapidapi.com/search").mock(
        return_value=httpx.Response(200, json={"status": "OK", "data": []})
    )
    
    searcher = JobSearcher(api_key="test-key")
    jobs = await searcher.search_jobs("xyzabc123 job nobody has")
    
    assert jobs == []


@pytest.mark.asyncio
@respx.mock
async def test_search_jobs_api_error():
    """Test handling when API returns error."""
    respx.get("https://jsearch.p.rapidapi.com/search").mock(
        return_value=httpx.Response(429, json={"message": "Rate limit exceeded"})
    )
    
    searcher = JobSearcher(api_key="test-key")
    jobs = await searcher.search_jobs("Python Developer")
    
    # Should return empty list, not crash
    assert jobs == []


@pytest.mark.asyncio
@respx.mock
async def test_search_jobs_timeout():
    """Test handling when API times out."""
    respx.get("https://jsearch.p.rapidapi.com/search").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )
    
    searcher = JobSearcher(api_key="test-key")
    jobs = await searcher.search_jobs("Python Developer")
    
    # Should return empty list, not crash
    assert jobs == []
```

---

### 2.3 Bot Function Unit Tests

```python
# tests/test_bot_functions.py

from bot import format_job_card, format_job_card_plain, build_job_keyboard

# Sample job dict
SAMPLE_JOB = {
    "title": "Python Developer",
    "company": "Infosys",
    "location": "Bangalore, Karnataka, India",
    "salary": "₹8L - ₹12L/year",
    "description": "We are looking for Python developers...",
    "job_type": "Full-time",
    "apply_url": "https://infosys.com/apply",
    "company_url": "https://infosys.com",
    "rating": "4.2",
    "posted": "2 din pehle",
    "skills": "Python, Django",
    "experience": "3+ years",
    "is_remote": False,
    "source": "LinkedIn"
}

def test_format_job_card_contains_required_fields():
    result = format_job_card(SAMPLE_JOB, 1)
    assert "Python Developer" in result
    assert "Infosys" in result
    assert "Bangalore" in result
    assert "₹8L" in result
    assert "Job #1" in result

def test_format_job_card_description_truncated():
    long_job = SAMPLE_JOB.copy()
    long_job["description"] = "x" * 500
    result = format_job_card(long_job, 1)
    # Description should be truncated
    assert "xxx" in result

def test_format_job_card_plain_no_markdown():
    result = format_job_card_plain(SAMPLE_JOB, 1)
    assert "*" not in result
    assert "_" not in result
    assert "`" not in result

def test_build_job_keyboard_has_apply_button():
    keyboard = build_job_keyboard(SAMPLE_JOB)
    # Flatten buttons
    all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    button_texts = [btn.text for btn in all_buttons]
    assert any("Apply" in t for t in button_texts)

def test_build_job_keyboard_no_apply_url():
    job_no_url = SAMPLE_JOB.copy()
    job_no_url["apply_url"] = ""
    job_no_url["company_url"] = ""
    keyboard = build_job_keyboard(job_no_url)
    all_buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    button_texts = [btn.text for btn in all_buttons]
    # Apply button should not be there
    assert not any("Apply" in t for t in button_texts)
    # But Naya Search should always be there
    assert any("Naya" in t for t in button_texts)
```

---

## 3. Manual Testing Checklist

Run these tests manually in Telegram after any code change:

### ✅ Core Search Tests

| Test | Input | Expected |
|---|---|---|
| Basic search | `Python Developer Mumbai` | ≥ 3 job cards |
| No location search | `Data Scientist` | Auto-adds "India", results shown |
| Remote search | `Frontend Developer remote` | Remote jobs prioritized |
| Very short query | `py` | "Thoda detail mein likho" message |
| Empty-ish query | ` ` (spaces) | Validation message |
| No results query | `xyzabc123qwerty` | "No jobs found" message |

### ✅ Command Tests

| Command | Expected |
|---|---|
| `/start` | Welcome message with user's name |
| `/help` | Full help guide |
| `/trending` | 5 trending jobs |
| `/search Python Developer Pune` | Job results |
| `/search` (no args) | "Usage: /search [query]" |
| `/clear` | "Session clear ho gayi!" |

### ✅ Button Tests

| Button | Expected |
|---|---|
| "Apply Now" | Opens job URL |
| "Company" | Opens company website |
| "Naya Search" | "Ab naya job likh do" prompt |
| "Aur Jobs Dekho" | Shows jobs 6-8 |

### ✅ Error Recovery Tests

| Scenario | How to Test | Expected |
|---|---|---|
| Wrong API key | Change RAPIDAPI_KEY to "wrong" | Friendly error message |
| No internet | Disconnect wifi, search | Friendly timeout message |
| Bot restart | Stop + restart bot | Sessions cleared, /start works fresh |

---

## 4. Running Tests

### Setup Test Environment:

```bash
cd "C:\Users\Amresh kumar\Downloads\AI"

# Install test dependencies
pip install pytest pytest-asyncio respx

# Run all tests
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_job_searcher.py -v

# Run specific test
pytest tests/test_bot_functions.py::TestEnhanceQuery::test_adds_india_when_no_location -v
```

---

## 5. Test File Structure

```
AI/
├── bot.py
├── job_searcher.py
└── tests/
    ├── __init__.py                    # Empty file
    ├── test_job_searcher.py           # Unit tests for JobSearcher class
    ├── test_bot_functions.py          # Unit tests for bot format functions
    ├── test_api_integration.py        # Mocked API integration tests
    └── fixtures/
        ├── mock_api_response.json     # Sample JSearch API response
        └── mock_empty_response.json   # Empty results response
```

---

## 6. Bug Classification

| Severity | Definition | Example | Fix SLA |
|---|---|---|---|
| **P0 Critical** | Bot crashes completely | Unhandled exception stops all users | Immediate |
| **P1 High** | Core feature broken | Search returns nothing, no error shown | Same day |
| **P2 Medium** | Feature degraded | Salary format wrong | 3 days |
| **P3 Low** | UI/text issue | Typo in message | Next release |

---

## 7. CI/CD Testing (Phase 2)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio respx pytest-cov
      - run: pytest tests/ -v --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```
