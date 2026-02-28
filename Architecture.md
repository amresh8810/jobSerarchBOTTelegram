# Architecture Overview
## AI Calling Agent — Hospital Appointment Booking System

---

## 1. System Philosophy

The AI Calling Agent is built on three architectural pillars:

| Pillar | Description |
|---|---|
| **Event-Driven** | Services communicate via async events (Kafka), decoupling producers from consumers |
| **Microservices** | Each domain (calls, appointments, auth) is an independently deployable service |
| **AI-First** | AI/NLP is not an add-on — it's the core interaction layer, with human handoff as fallback |

---

## 2. Architecture Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                           │
│  Admin Dashboard (React SPA) | Supervisor Web App | Patient SMS  │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTPS / WSS
┌───────────────────────────────▼──────────────────────────────────┐
│                      API GATEWAY LAYER                            │
│           Authentication · Rate Limiting · Routing               │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                     APPLICATION LAYER                             │
│  Auth   │  Call Orchestrator  │  Appointment  │  Notification    │
│  Service│  (State Machine)    │  Service      │  Service         │
└─────────────────────────────┬─┬───────────────────────────────────┘
                              │ │
        ┌─────────────────────┘ └──────────────────────┐
        ▼                                              ▼
┌───────────────────────┐               ┌─────────────────────────┐
│     AI LAYER          │               │   TELEPHONY LAYER        │
│  STT (Google)         │               │  Twilio / Exotel         │
│  NLP (Dialogflow CX)  │               │  Call Control            │
│  TTS (WaveNet)        │               │  Recording               │
│  Scoring Engine       │               │  DTMF / IVR              │
└───────────────────────┘               └─────────────────────────┘
        │                                              │
        └──────────────────┬───────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                   │
│  PostgreSQL (primary) │ Redis (cache) │ S3 (recordings & files)  │
│  Kafka (event bus)    │ Elasticsearch (optional: transcripts)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Domain Services

### 3.1 Call Orchestrator
The brain of the system — manages the entire lifecycle of an AI call.

**Responsibilities:**
- Dequeue patient from campaign call queue
- Pre-call validation (DND check, retry count)
- Initiate call via Telephony Service
- Drive conversation by executing script nodes
- Coordinate between STT → NLP → TTS in real-time
- Handle timeout, errors, and fallbacks
- Post-call processing (scoring, updating appointment, triggering SMS)

**State Machine:**
```
[QUEUED]
    ↓ DND check passes
[INITIATING]
    ↓ Twilio dials number
[RINGING]
    ↓ Patient answers
[ACTIVE]
    ↓ Script executes
[ENDING]
    ↓ Script complete / escalated
[COMPLETED] or [ESCALATED] or [FAILED]
```

---

### 3.2 AI Conversation Engine

```
                    Patient Voice Input
                          ↓
          ┌───────────────────────────────┐
          │    STT (Real-time streaming)   │
          │   Google Cloud Speech-to-Text  │
          └───────────────┬───────────────┘
                          ↓ Text Transcript
          ┌───────────────────────────────┐
          │         NLP Engine             │
          │    (Dialogflow CX / LLM)       │
          │   Intent + Entity Detection    │
          └───────────────┬───────────────┘
                          ↓ Intent + Entities
          ┌───────────────────────────────┐
          │      Script Flow Engine        │
          │   Execute next script step     │
          │   API calls if needed          │
          └───────────────┬───────────────┘
                          ↓ AI Response Text
          ┌───────────────────────────────┐
          │    TTS (Text-to-Speech)        │
          │   Google WaveNet / Azure       │
          └───────────────┬───────────────┘
                          ↓ Audio
                    Played to Patient
```

---

### 3.3 Appointment Service (HMS Connector)

Acts as a translation layer between the AI Agent and the Hospital Management System (HMS).

```
AI Agent Request
      ↓
Appointment Service API
      ↓
HMS Adapter (HL7 FHIR / REST)
      ↓
Hospital Management System (HMS)
      ↓
Response mapped back
      ↓
AI Agent receives appointment data
```

**Adapter Pattern**: The adapter abstracts the HMS API so future HMS changes don't affect the core system.

---

## 4. Event Flow Architecture

### Event: Call Completed
```
[Call Orchestrator]
    → Publishes: call.completed
    
[Appointment Service] consumes:
    → Updates appointment status to "confirmed"
    
[Notification Service] consumes:
    → Sends confirmation SMS to patient
    
[Analytics Service] consumes:
    → Increments campaign stats
    → Updates doctor's confirmed count
    
[Scoring Engine] consumes:
    → Calculates call quality score
    → Updates no-show risk score
```

### Kafka Topics

| Topic | Partitions | Producers | Consumers |
|---|---|---|---|
| `calls.initiated` | 10 | Call Orchestrator | Monitoring |
| `calls.completed` | 10 | Call Orchestrator | Appointment, Notification, Analytics, Scoring |
| `calls.failed` | 5 | Call Orchestrator | Notification, Analytics |
| `calls.escalated` | 5 | Call Orchestrator | Supervisor Dashboard |
| `appointments.changed` | 10 | Appointment Service | Notification, HMS Sync |
| `campaigns.queued` | 20 | Campaign Manager | Call Orchestrator |
| `sms.send` | 5 | Notification Service | SMS Gateway |

---

## 5. Scalability Architecture

### Horizontal Scaling Points

| Component | Scaling Mechanism |
|---|---|
| Call Orchestrator | K8s HPA (scale on active call count) |
| STT/TTS | Serverless (Cloud Run / Lambda) |
| Appointment API | K8s HPA (scale on CPU/requests) |
| Kafka consumers | Consumer group partition rebalancing |
| Database reads | PostgreSQL read replicas + Redis cache |

### Traffic Patterns
- Peak calls: 9 AM – 11 AM and 4 PM – 6 PM
- Pre-scale: +50% replicas 30 min before peak
- Auto-scale: HPA triggers at 70% CPU utilization

---

## 6. Data Architecture

### Write Path (Command)
```
API Request → Validation → Service → Repository → PostgreSQL (write)
                                          ↓
                                   Kafka Event published
```

### Read Path (Query)
```
API Request → Check Redis Cache
                  ↓ (miss)
              PostgreSQL Read Replica
                  ↓
              Cache result in Redis (TTL: 15m)
                  ↓
              Return response
```

---

## 7. Security Architecture

```
User Request
    ↓
WAF (DDoS Protection, SQL Injection filter)
    ↓
API Gateway (TLS termination, JWT validation)
    ↓
Service (RBAC authorization check)
    ↓
Database (row-level security, encrypted PII columns)
```

### Key Security Controls

| Control | Implementation |
|---|---|
| Authentication | JWT RS256 + OAuth2 |
| Authorization | RBAC per endpoint |
| Transport | TLS 1.3 everywhere |
| PII at Rest | pgcrypto column encryption |
| Secrets | AWS Secrets Manager |
| Audit | All actions logged to `audit_logs` |
| Recording Access | Pre-signed S3 URLs (1hr TTL) |

---

## 8. Disaster Recovery & High Availability

| Component | HA Strategy | RTO | RPO |
|---|---|---|---|
| API Services | Multi-AZ K8s, ≥2 replicas | < 1 min | 0 |
| PostgreSQL | Primary + 1 read replica + automated backups | < 5 min | < 1 min |
| Redis | Redis Sentinel (automatic failover) | < 30 sec | 0 |
| Kafka | 3-broker cluster, replication factor 3 | < 1 min | 0 |
| Call recordings (S3) | Cross-region replication | N/A | < 5 min |

### Backup Schedule
- PostgreSQL: Hourly snapshots, 30-day retention
- S3 recordings: Cross-region copy within 1 hour
- Configuration: Daily git backup

---

## 9. Monitoring & Observability

```
Application Metrics → Prometheus
      ↓
Grafana Dashboards (live metrics)

Application Logs → Fluentd → Elasticsearch → Kibana

Distributed Traces → Jaeger / AWS X-Ray

Alerts → PagerDuty / Slack
```

### Key Dashboards
1. **Call Operations**: Active calls, queue depth, error rates
2. **AI Performance**: STT accuracy, NLP confidence scores, TTS latency
3. **Campaign Progress**: Calls completed, booking rate, no-shows
4. **Infrastructure**: CPU, memory, DB connections, Kafka lag

### SLO Definitions

| Service | SLO | Alert Threshold |
|---|---|---|
| API availability | 99.9% | < 99.5% |
| Call success rate | ≥ 85% | < 80% |
| STT latency P95 | < 300ms | > 500ms |
| API latency P95 | < 200ms | > 400ms |
| Error rate | < 1% | > 2% |