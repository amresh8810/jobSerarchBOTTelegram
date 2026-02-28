# 02 — User Stories & Acceptance Criteria
## Telegram Job Search AI Agent

---

## Epic Overview

| Epic ID | Epic Name | Priority |
|---|---|---|
| E-01 | Job Search Core | P0 |
| E-02 | Result Display | P0 |
| E-03 | Bot Commands | P0 |
| E-04 | Error Handling | P0 |
| E-05 | Job Alerts | P1 |
| E-06 | Filters & Personalization | P1 |
| E-07 | Analytics & Feedback | P2 |

---

## E-01: Job Search Core

### US-01-01: Natural Language Search
**As a** job seeker,  
**I want to** type my job requirement in plain text (e.g., "Python Developer Mumbai"),  
**So that** I get relevant job listings without filling complex forms.

**Acceptance Criteria:**
- [ ] Bot accepts any plain text message as a search query
- [ ] Minimum 2 characters required to trigger search
- [ ] Query is automatically enhanced with "India" if no location specified
- [ ] Results returned within 5 seconds
- [ ] Shows "Searching..." indicator while processing
- [ ] Returns minimum 1 result or shows "no jobs found" message

---

### US-01-02: Multi-Platform Job Aggregation
**As a** job seeker,  
**I want** jobs from LinkedIn, Indeed, Glassdoor, Naukri etc. in one place,  
**So that** I don't miss opportunities on any platform.

**Acceptance Criteria:**
- [ ] JSearch API called with user query
- [ ] Results include source platform (LinkedIn / Indeed / Glassdoor)
- [ ] Minimum 5 results shown per search (if available)
- [ ] Maximum 8 results fetched per search
- [ ] Duplicate jobs from same company are deduplicated

---

### US-01-03: /search Command
**As a** power user,  
**I want** to use `/search Python Developer Pune` command directly,  
**So that** I can search quickly without extra steps.

**Acceptance Criteria:**
- [ ] `/search` command accepts arguments after the command
- [ ] `/search` without args → shows usage instruction
- [ ] Works same as plain text search
- [ ] Response format identical to plain text search

---

## E-02: Result Display

### US-02-01: Job Card Format
**As a** job seeker,  
**I want** each job shown as a clearly formatted card,  
**So that** I can quickly understand the key details.

**Acceptance Criteria:**
- [ ] Each card shows: Job Title, Company, Location, Salary, Job Type, Description
- [ ] Description truncated to 300 characters with "..." at end
- [ ] Posted date shown in human-readable form ("2 din pehle")
- [ ] Company rating shown if available
- [ ] Numbered index shown (#1, #2, etc.)

---

### US-02-02: Apply Now Button
**As a** job seeker,  
**I want** a direct "Apply Now" button on each job card,  
**So that** I can apply instantly without searching for the link.

**Acceptance Criteria:**
- [ ] "Apply Now" inline button present on every job card
- [ ] Button opens original job posting URL
- [ ] If no apply URL → button not shown
- [ ] "Company" button shown if company website available
- [ ] "Naya Search" button always shown

---

### US-02-03: Salary Display
**As a** job seeker,  
**I want** to see salary information clearly,  
**So that** I can decide if the role matches my expectations.

**Acceptance Criteria:**
- [ ] INR salaries shown in Lakh format (₹8L - ₹12L/year)
- [ ] USD salaries shown in K format ($80K - $120K/year)
- [ ] Min-max range shown when available
- [ ] "Not mentioned" shown when salary unavailable
- [ ] Salary period specified (per year / per month / per hour)

---

### US-02-04: Load More / Pagination
**As a** job seeker,  
**I want** to load more results if needed,  
**So that** I can see all available options.

**Acceptance Criteria:**
- [ ] First 5 jobs shown immediately
- [ ] "Aur Jobs Dekho" button shown if more than 5 results
- [ ] Button loads next batch (jobs 6-8)
- [ ] Session saved per user to maintain search context
- [ ] Session expires after 1 hour of inactivity

---

## E-03: Bot Commands

### US-03-01: /start Command
**As a** new user,  
**I want** a welcoming introduction when I first open the bot,  
**So that** I understand how to use it.

**Acceptance Criteria:**
- [ ] Personalized greeting with user's first name
- [ ] Lists all available commands with descriptions
- [ ] Shows 5 example search queries
- [ ] Response in under 1 second
- [ ] Works as reset if existing user types /start

---

### US-03-02: /trending Command
**As a** job seeker,  
**I want** to see trending / high-demand jobs in India,  
**So that** I can explore roles that are in demand.

**Acceptance Criteria:**
- [ ] Shows top 5 trending IT/business jobs in India
- [ ] Pre-defined popular query used (e.g., "Software Engineer India 2025")
- [ ] Same card format as regular search results
- [ ] Response in under 6 seconds
- [ ] Header clearly says "Trending Jobs in India"

---

### US-03-03: /help Command
**As a** user,  
**I want** a detailed help guide,  
**So that** I can understand all bot features.

**Acceptance Criteria:**
- [ ] Shows all commands with descriptions
- [ ] Shows 5 search query examples
- [ ] Explains what each result field means
- [ ] Compact enough to read in one screen

---

### US-03-04: /clear Command
**As a** user,  
**I want** to clear my search session,  
**So that** I can start fresh without old context.

**Acceptance Criteria:**
- [ ] Clears user session from memory
- [ ] Confirmation message shown ("Session clear ho gayi!")
- [ ] After clear, /search works fresh
- [ ] Works even if no session exists

---

## E-04: Error Handling

### US-04-01: No Results Found
**As a** user,  
**I want** a helpful message when no jobs are found,  
**So that** I know how to refine my search.

**Acceptance Criteria:**
- [ ] Clear "no results" message shown
- [ ] Suggests 3 ways to improve the search
- [ ] Button to try a new search
- [ ] Never shows empty response

---

### US-04-02: API Timeout / Error
**As a** user,  
**I want** a friendly message if the search fails,  
**So that** I can try again without confusion.

**Acceptance Criteria:**
- [ ] Timeout after 20 seconds max
- [ ] User sees "try again" message (not technical error)
- [ ] Error logged silently in backend
- [ ] Bot does not crash — continues working for other users

---

### US-04-03: Short Query Handling
**As a** user,  
**I want** the bot to ask for more details if my query is too short,  
**So that** I know I need to be more specific.

**Acceptance Criteria:**
- [ ] Queries less than 2 characters → prompt to add more details
- [ ] Message includes example of a good query
- [ ] No API call made for too-short queries

---

## E-05: Job Alerts (Phase 2)

### US-05-01: Subscribe to Daily Job Digest
**As a** regular job seeker,  
**I want** to subscribe to daily job alerts for my preferred roles,  
**So that** I don't have to search manually every day.

**Acceptance Criteria:**
- [ ] `/subscribe Python Developer Mumbai` command activates alert
- [ ] Bot sends digest every morning at 9 AM IST
- [ ] Max 5 jobs per alert
- [ ] `/unsubscribe` command removes alert
- [ ] User can have up to 3 active subscriptions

---

## Definition of Done (DoD)

All stories complete when:
1. ✅ Code written and merged
2. ✅ Manual testing done on real Telegram
3. ✅ Edge cases handled (no results, API error, long text)
4. ✅ Does not crash bot for other concurrent users
5. ✅ Response within SLA (5 seconds)
