# Product Requirements Document (PRD)
## AI Calling Agent — Hospital Appointment Booking System

**Version**: 1.0  
**Date**: February 2026  
**Status**: Approved for Development  

---

## 1. Product Overview

### 1.1 Product Name
**AI Calling Agent** — *Smart Hospital Appointment Manager*

### 1.2 Product Vision
> *"Eliminate missed appointments and call center wait times by deploying an intelligent AI voice agent that proactively manages patient appointments around the clock."*

### 1.3 Problem We're Solving

Hospitals face a chronic challenge: high no-show rates (15–30%), expensive call center operations, and poor patient communication. The AI Calling Agent solves this by:
- Automating outbound appointment reminders
- Allowing patients to confirm, reschedule, or cancel via voice
- Providing hospital admins real-time visibility into appointment status
- Reducing the cost-per-appointment-managed by 60%+

---

## 2. Target Market

**Primary Market**: Private hospitals, polyclinics, and multi-specialty healthcare centers in India (Tier 1 and Tier 2 cities)

**Addressable Market**: 
- 75,000+ private hospitals in India
- Average 100–500 outpatient appointments/day per hospital
- $200M+ annual call center spend in Indian healthcare

---

## 3. User Personas

### Persona 1: Dr. Anjali Mehta (Hospital Administrator)
- **Age**: 42, runs operations at a 200-bed private hospital
- **Pain**: Spends ₹8L/month on call center staff; still gets 25% no-shows
- **Goal**: Reduce no-shows, cut call center costs, maintain quality patient experience
- **Success**: "No-shows dropped from 25% to 10% in the first month"

### Persona 2: Rajesh Sharma (Call Center Supervisor)
- **Age**: 35, manages 15 call center agents
- **Pain**: Agents spend most of their time on repetitive reminder calls
- **Goal**: Focus agents on complex patient interactions, not routine reminders
- **Success**: "My team now handles escalations only — AI does all the routine work"

### Persona 3: Mrs. Priya Gupta (Patient)
- **Age**: 55, regular outpatient visitor
- **Pain**: Calls hospital to reschedule but stays on hold for 20+ minutes
- **Goal**: Manage appointments quickly without hassle
- **Success**: "The AI called me, I said 'reschedule,' and it was done in 2 minutes"

---

## 4. Product Goals

| Goal | Metric | Target |
|---|---|---|
| Reduce no-show rates | No-show % | From ~25% → < 12% |
| Reduce staffing cost | Call cost per appointment | From ₹80 → ₹12 |
| Improve patient experience | CSAT score | ≥ 4.2/5.0 |
| Enable 24/7 availability | Hours of operation | 24h vs 9h human shift |
| Increase call efficiency | Avg call duration | ≤ 3 minutes |

---

## 5. Features & Requirements

### 5.1 Core AI Voice Agent

#### R-01: Outbound Calling
- **Requirement**: System must initiate outbound calls to patients for appointment reminders
- **Trigger**: Campaign schedule, or manual trigger by admin
- **Pre-condition**: Patient not on DND registry
- **Retry policy**: Up to 3 retries, 10 minutes apart
- **Call window**: 9 AM – 7 PM (configurable per hospital)

#### R-02: Natural Language Understanding
- **Requirement**: AI must understand free-form patient speech (not just DTMF)
- **Languages**: English (Indian accent) — Phase 1; Hindi — Phase 2
- **Intent accuracy**: ≥ 92% on common intents
- **Fallback**: DTMF option if speech not understood after 2 attempts

#### R-03: Appointment Actions via Voice
The AI must support:
1. **Confirm** appointment: "Yes, confirm"
2. **Reschedule**: Offer next 3 available slots; patient selects by saying date/time
3. **Cancel**: With optional reason capture
4. **Get Directions**: Play recorded directions to hospital (canned response)

#### R-04: Human Escalation
- **Trigger**: Patient says "human", "agent", "transfer", or AI confidence < 0.65
- **Action**: Warm transfer to available agent with call summary
- **Wait time**: Must inform patient if wait > 30 seconds

#### R-05: Identity Verification
- **Method**: 2-factor validation (name + DOB, or name + phone)
- **Maximum attempts**: 3
- **Failure action**: SMS patient with hospital callback number

---

### 5.2 Admin Dashboard

#### R-06: Live Call Monitor
- Real-time view of all active calls
- Status: active, ringing, escalated, completed
- Supervisor can barge-in on any live call

#### R-07: Campaign Manager
- Create bulk call campaigns for groups of patients
- Filters: department, doctor, appointment date, appointment status
- Schedule campaigns to run at specific times
- Pause/resume campaigns in progress

#### R-08: Call History & Analytics
- Full call log with recording playback and transcript
- Sentiment score per call
- Booking rate, no-show rate trends
- Exportable reports (CSV, PDF)

#### R-09: AI Script Editor
- Visual flow builder for creating conversation scripts
- Variable substitution ({{patient_name}}, {{appointment_date}})
- Test scripts with simulated calls
- Version history with rollback

---

### 5.3 Integrations

#### R-10: HMS Integration
- Connect to hospital's HMS to read/write appointment data
- Protocol: HL7 FHIR R4 or custom REST API (HMS-dependent)
- Real-time slot sync (availability updated within 30 seconds)

#### R-11: SMS Follow-up
- Send SMS confirmation/summary after every call
- Template: customizable by hospital with their branding

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | API P95 < 200ms; call latency < 3s |
| **Scalability** | 500 concurrent calls; 10,000/day |
| **Security** | HIPAA-aligned; JWT auth; TLS 1.3; column-level PII encryption |
| **Compliance** | TRAI regulations; DND registry checks |
| **Uptime** | 99.9% SLA |
| **Languages** | English (Phase 1), Hindi (Phase 2) |
| **Browser Support** | Chrome 115+, Firefox 115+, Edge 115+, Safari 16+ |

---

## 7. User Journey — End to End

```
[Campaign Configured] → [Call Queue Generated]
         ↓
[AI Calls Patient] → [Answers] → [Identity Verified]
         ↓
[AI Presents Appointment Info]
         ↓
[Patient: Confirm] → [HMS Updated] → [SMS Sent] → ✅ Done
[Patient: Reschedule] → [Slots Offered] → [Slot Selected] → [HMS Updated] → [SMS Sent] → ✅ Done
[Patient: Cancel] → [Reason Captured] → [HMS Updated] → [SMS Sent] → ✅ Done
[Patient: Human] → [Warm Transfer] → [Agent Handles] → ✅ Done
[No Answer] → [Retry x3] → [Queue for Human] → 📋 Pending
```

---

## 8. Constraints

| Constraint | Detail |
|---|---|
| Budget | ₹15 Lakhs for MVP development |
| Timeline | 12 weeks to MVP go-live |
| Team | 8 engineers + 1 PM |
| Regulatory | Must comply with TRAI + Personal Data Protection Bill |
| HMS | Must work with client's existing HMS (no replacement) |

---

## 9. Success Metrics — Launch + 90 Days

| KPI | Baseline | Target |
|---|---|---|
| No-show rate | 25% | ≤ 12% |
| Call completion rate | N/A (new system) | ≥ 85% |
| Booking confirmation rate | N/A | ≥ 75% |
| Cost per appointment managed | ₹80 | ≤ ₹15 |
| CSAT (patients) | N/A | ≥ 4.2/5.0 |
| CSAT (hospital staff) | N/A | ≥ 4.0/5.0 |
| Average call duration | N/A | ≤ 3 min |

---

## 10. Roadmap

```
Q1 2026: MVP — Core outbound calling, appointment management, admin dashboard
Q2 2026: Growth — Hindi support, WhatsApp, inbound IVR, advanced analytics
Q3 2026: Scale — Custom LLM, multi-hospital SaaS, mobile app
Q4 2026: Enterprise — Voice biometrics, deeper EHR integration, insurance workflows
```

---

## 11. Stakeholders & Sign-off

| Role | Name | Responsibility |
|---|---|---|
| Product Manager | — | Overall product vision |
| Engineering Lead | — | Technical feasibility |
| Hospital CTO | — | Business requirements |
| Compliance Officer | — | Regulatory sign-off |
| Design Lead | — | UX/UI approval |