# MVP Technical Document
## AI Calling Agent — Hospital Appointment Booking System

---

## 1. MVP Scope Summary

The Minimum Viable Product (MVP) delivers a working end-to-end AI calling system for hospital appointment management. The MVP is scoped for a **single hospital**, English + Hindi support, and outbound calling only.

**MVP In One Sentence**: *An AI agent that calls patients to remind, confirm, reschedule, or cancel appointments — with an admin dashboard to manage and monitor everything.*

---

## 2. MVP Feature List

| # | Feature | Status |
|---|---|---|
| 1 | Outbound AI calling (Twilio/Exotel) | ✅ In Scope |
| 2 | Patient identity verification | ✅ In Scope |
| 3 | Appointment confirmation via call | ✅ In Scope |
| 4 | Appointment rescheduling via call | ✅ In Scope |
| 5 | Appointment cancellation via call | ✅ In Scope |
| 6 | Human escalation (warm transfer) | ✅ In Scope |
| 7 | Call recording + transcript | ✅ In Scope |
| 8 | SMS confirmation (post-call) | ✅ In Scope |
| 9 | Admin dashboard | ✅ In Scope |
| 10 | Live call monitor | ✅ In Scope |
| 11 | Call campaign manager | ✅ In Scope |
| 12 | Basic AI script editor | ✅ In Scope |
| 13 | Basic analytics dashboard | ✅ In Scope |
| 14 | Patient & appointment CRUD | ✅ In Scope |
| 15 | RBAC (Admin + Supervisor) | ✅ In Scope |
| 16 | DND registry check | ✅ In Scope |
| 17 | Retry logic (3 attempts) | ✅ In Scope |
| 18 | Basic sentiment analysis | ✅ In Scope |
| — | Hindi language | ❌ Phase 2 |
| — | WhatsApp integration | ❌ Phase 2 |
| — | Inbound calls | ❌ Phase 2 |

---

## 3. Technical Stack (MVP)

| Layer | Technology | Version |
|---|---|---|
| Frontend | React.js + TypeScript | 18.x |
| UI Library | Tailwind CSS + shadcn/ui | 3.x |
| State Management | Zustand + React Query | 5.x |
| Backend API | Python FastAPI | 0.110+ |
| Node Services | Node.js + Express | 20.x LTS |
| Database | PostgreSQL | 15.x |
| Cache | Redis | 7.x |
| Message Broker | Apache Kafka | 3.6+ |
| AI/NLP | Google Dialogflow CX | — |
| STT | Google Cloud Speech-to-Text | en-IN |
| TTS | Google WaveNet Neural | en-IN-Wavenet-D |
| Telephony | Twilio Programmable Voice | — |
| SMS | Twilio Messaging / 2Factor.in | — |
| Storage | AWS S3 | — |
| Container | Docker + Kubernetes (EKS) | K8s 1.28 |
| CI/CD | GitHub Actions + ArgoCD | — |
| Monitoring | Prometheus + Grafana | — |

---

## 4. Architecture (MVP Simplified)

```
Patient Phone ←──→ Twilio ←──→ Call Orchestrator
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                        STT          NLP         TTS
                    (Google)    (Dialogflow)  (WaveNet)
                          │           │
                          └─────┬─────┘
                                ▼
                      Appointment Service
                                │
                        HMS Adapter (mock)
                                │
                          PostgreSQL
                                │
                     Notification Service
                                │
                         Twilio SMS
```

---

## 5. MVP API Endpoints (Core)

### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Patients
- `GET /api/v1/patients`
- `POST /api/v1/patients`
- `GET /api/v1/patients/:id`
- `PUT /api/v1/patients/:id`

### Appointments
- `GET /api/v1/appointments`
- `POST /api/v1/appointments`
- `GET /api/v1/appointments/:id`
- `PATCH /api/v1/appointments/:id/reschedule`
- `PATCH /api/v1/appointments/:id/cancel`

### Calls
- `GET /api/v1/calls`
- `POST /api/v1/calls/initiate`
- `GET /api/v1/calls/:id`
- `GET /api/v1/calls/:id/transcript`

### Campaigns
- `GET /api/v1/campaigns`
- `POST /api/v1/campaigns`
- `POST /api/v1/campaigns/:id/launch`
- `POST /api/v1/campaigns/:id/pause`

### Analytics
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/calls`

---

## 6. Database Tables (MVP Core)

| Table | Records Estimated (Year 1) |
|---|---|
| `hospitals` | 1 |
| `departments` | 10–20 |
| `doctors` | 20–100 |
| `patients` | 5,000–20,000 |
| `appointments` | 50,000–200,000 |
| `calls` | 100,000–500,000 |
| `call_transcripts` | 500,000–2,500,000 |
| `campaigns` | 50–500 |
| `notifications` | 200,000–1,000,000 |

---

## 7. AI Call Flow (Detailed MVP Flow)

```
Step 1:  System triggers campaign (scheduled or manual)
Step 2:  Call Orchestrator dequeues patient
Step 3:  DND check (if on DND → skip, log, next patient)
Step 4:  Twilio initiates outbound call
Step 5:  [Patient does not answer] → retry after 10 min
Step 6:  [Patient answers] → call state: ACTIVE
Step 7:  TTS says greeting:
         "Hello! May I speak with {patient_name}?"
Step 8:  STT captures patient response
Step 9:  NLP classifies → intent: patient_confirmed_identity
Step 10: TTS says:
         "You have an appointment with Dr. {doctor_name} on {date} at {time}.
          Would you like to confirm this appointment?"
Step 11: STT + NLP → intent: confirm_appointment
Step 12: Appointment Service → update status to "confirmed" in DB
Step 13: TTS says: "Great! Your appointment is confirmed. You'll receive an SMS. Goodbye!"
Step 14: Call ends
Step 15: SMS sent to patient with appointment details
Step 16: Scoring Engine runs quality + sentiment scores
Step 17: Campaign stats updated (+1 completed, +1 confirmed)
```

---

## 8. Non-Functional Requirements (MVP Targets)

| Requirement | Target |
|---|---|
| Call latency (dial to AI voice) | < 3 seconds |
| STT latency (spoken to text) | < 300ms streaming |
| NLP intent confidence threshold | > 0.75 |
| API response time (P95) | < 200ms |
| Concurrent calls (MVP) | 100 (scale to 500 in Phase 2) |
| System uptime | 99.9% |
| Call recording quality | G.711 (PCMU), 8kHz |
| Transcript accuracy (English) | ≥ 92% WER |
| SMS delivery rate | ≥ 98% |

---

## 9. Security Requirements (MVP)

| Item | Implementation |
|---|---|
| Authentication | JWT RS-256 with 8hr expiry |
| Authorization | RBAC (Admin, Supervisor roles in MVP) |
| HTTPS | TLS 1.3 mandatory |
| Password hashing | bcrypt (cost factor 12) |
| PII in logs | Masked (phone: `+91-XXXX-X6789`) |
| Call recordings | Stored encrypted in S3 |
| DB PII | Encrypted columns (pgcrypto) |
| API rate limiting | 100 req/min per IP |

---

## 10. MVP Limitations & Known Constraints

| Limitation | Impact | Resolution in Phase |
|---|---|---|
| English only | Won't serve Hindi patients | Phase 2 |
| Outbound calling only | Patients can't call in to AI | Phase 2 |
| Single hospital | No multi-tenant | Phase 3 |
| Basic script editor | Limited flow complexity | Phase 2 |
| Dialogflow CX (not custom LLM) | Less natural conversation | Phase 2 |
| No mobile app | Admins need browser | Phase 3 |
| Manual HMS integration | Requires IT setup | Ongoing |

---

## 11. Go-Live Checklist

- [ ] All P0 features developed and tested
- [ ] Load test: 100 concurrent calls passed
- [ ] Security audit cleared
- [ ] TRAI compliance reviewed by legal
- [ ] Hospital IT has integrated HMS connector
- [ ] Twilio account and numbers provisioned (India DIDs)
- [ ] DND registry API integrated and tested
- [ ] SMS gateway tested (delivery > 98%)
- [ ] Admin training completed (at least 3 staff)
- [ ] Runbook for on-call engineers prepared
- [ ] Monitoring dashboards and alerts configured
- [ ] Backup and recovery tested
- [ ] Data retention policies configured
- [ ] Production credentials rotated (no dev creds in prod)
- [ ] SLA documentation signed with hospital

---

## 12. MVP Success Metrics (30-Day Post-Launch)

| Metric | Target |
|---|---|
| Total calls made | ≥ 5,000 |
| Call completion rate | ≥ 80% |
| Appointment confirmation rate | ≥ 70% |
| No-show rate reduction | ≥ 20% vs baseline |
| System uptime | ≥ 99.9% |
| Escalation to human rate | ≤ 20% |
| CSAT (hospital staff) | ≥ 4.0/5.0 |
| Critical bugs in production | 0 |