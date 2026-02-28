# 01 — Product Requirements Document (PRD)
## Telegram Job Search AI Agent

**Version**: 1.0 | **Date**: February 2026 | **Status**: In Development

---

## 1. Executive Summary

Telegram Job Search AI Agent एक intelligent chatbot है जो users के साथ Telegram chat के through बात करके internet से real-time job listings ढूंढता है। User सिर्फ job role और location type करता है — bot automatically LinkedIn, Indeed, Glassdoor जैसे platforms से jobs search करके formatted results देता है।

---

## 2. Problem Statement

| Pain Point | Impact |
|---|---|
| Job portals पर manually search करना time-consuming है | Daily 1-2 घंटे बर्बाद |
| हर site अलग-अलग open करनी पड़ती है | Fragmented experience |
| Salary information छुपी होती है | Informed decision नहीं ले पाते |
| Mobile पर job search clunky है | Poor UX on phone |
| Alert/notification system नहीं | नई jobs miss हो जाती हैं |

---

## 3. Product Vision

> *"Apne Telegram pe type karo — Python Developer Mumbai — aur seconds mein top jobs haazir!"*

---

## 4. Goals & Success Metrics

### 4.1 Business Goals
- Users को **एक जगह** से सभी major job portals search करने दो
- Job search time **80% कम** करो
- **Salary transparency** बढ़ाओ
- **5,000+ active users** पहले 3 महीनों में

### 4.2 KPIs

| Metric | Target |
|---|---|
| Daily Active Users (DAU) | ≥ 500 |
| Avg searches per user/day | ≥ 3 |
| Search results relevancy | ≥ 85% |
| Bot response time | ≤ 5 seconds |
| User retention (7-day) | ≥ 40% |
| API uptime | ≥ 99% |

---

## 5. Target Users

### Primary Users

| User | Background | Job Search Goal |
|---|---|---|
| **Fresh Graduates** | 21-25 years, B.Tech/MBA | Entry-level IT, Management jobs |
| **Experienced Professionals** | 25-40 years | Career switch, salary hike |
| **Freelancers** | Any age | Remote, part-time, contract work |
| **Job Seekers in Tier-2 Cities** | Limited portal access | Remote jobs, metro city jobs |

### Secondary Users

| User | Use Case |
|---|---|
| Recruiters | Quick market salary benchmarking |
| Career Counselors | Show students real market data |
| College Placement Cells | Bulk job search for students |

---

## 6. Core Features

### 6.1 Must-Have (MVP - v1.0)

| # | Feature | Description |
|---|---|---|
| F-01 | **Natural Language Job Search** | User types role + location in plain text |
| F-02 | **Multi-platform Results** | Search LinkedIn, Indeed, Glassdoor simultaneously |
| F-03 | **Job Card Display** | Title, Company, Location, Salary, Description |
| F-04 | **Direct Apply Link** | One-click apply button in chat |
| F-05 | **Pagination** | "Load More" button for more results |
| F-06 | **Trending Jobs** | India's top job roles today |
| F-07 | **/search Command** | Direct command-based search |
| F-08 | **Error Handling** | Friendly messages when no jobs found |

### 6.2 Should-Have (v1.5)

| # | Feature |
|---|---|
| F-09 | Job Alerts (Daily digest) |
| F-10 | Salary filter (e.g., "above 10 lakh") |
| F-11 | Job type filter (Remote / Full-time / Internship) |
| F-12 | Save favorites / wishlist |
| F-13 | "Similar Jobs" suggestions |

### 6.3 Nice-to-Have (v2.0)

| # | Feature |
|---|---|
| F-14 | Resume upload → matching jobs |
| F-15 | Interview tips per role |
| F-16 | Company reviews summary (Glassdoor) |
| F-17 | Salary negotiation guide |
| F-18 | Hindi language support |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Search results in ≤ 5 seconds |
| **Reliability** | 99% bot uptime |
| **Scalability** | Handle 1,000 concurrent users |
| **Security** | No user PII stored; API keys in env only |
| **Privacy** | Only search queries logged (no personal data) |
| **Rate Limiting** | Handle API rate limits gracefully |
| **Usability** | No training needed — works like WhatsApp |

---

## 8. Constraints & Assumptions

### Constraints
- JSearch Free API: **200 requests/month** (upgrade for production)
- Telegram Rate Limit: 30 messages/second per bot
- Python 3.10+ required
- No database in MVP (stateless)

### Assumptions
- Users have Telegram installed
- Searches primarily in English (Hindi Phase 2)
- Indian job market is primary focus
- Internet connection required

---

## 9. Out of Scope (MVP)

- Resume building / ATS optimization
- Direct application submission
- Video interview scheduling
- Payment / premium subscription system
- WhatsApp / other platform support

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| RapidAPI free limit exceeded | High | Medium | Rate limiting + upgrade plan |
| JSearch API results irrelevant | Medium | High | Query enhancement + fallback |
| Telegram API downtime | Low | High | Retry logic + health checks |
| No salary data available | High | Medium | Show "Not mentioned" gracefully |
| Markdown parsing errors in bot | Medium | Low | Plain text fallback |

---

## 11. Success Criteria (30 Days Post-Launch)

- [ ] ≥ 500 users registered
- [ ] ≥ 1,500 searches per day
- [ ] Average response time < 5s
- [ ] Zero P0 bugs in production
- [ ] User satisfaction ≥ 4/5 (via /feedback command)
