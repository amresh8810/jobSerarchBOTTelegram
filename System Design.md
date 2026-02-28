# System Design Document
## AI Calling Agent — Hospital Appointment Booking System

**Version**: 1.0  
**Date**: February 2026

---

## 1. System Overview

The AI Calling Agent is a distributed, microservices-based platform that orchestrates AI-powered phone calls to hospital patients. The system integrates telephony (Twilio/Exotel), speech AI (Google STT/TTS), natural language understanding (Dialogflow CX), and hospital management systems (HMS) to deliver a seamless automated appointment management experience.

---

## 2. High-Level Design

### 2.1 Context Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                  AI CALLING AGENT SYSTEM                          │
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Admin      │  │  Call       │  │  Patient                 │  │
│  │  Dashboard  │  │  Orchestr.  │  │  (via phone)             │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │
│         │                │                      ↕                 │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │                │                      │
  ┌───────▼──┐     ┌───────▼──┐           ┌───────▼──┐
  │ REST API │     │  Kafka   │           │  Twilio  │
  └──────────┘     └──────────┘           └──────────┘
          │                │
  ┌───────▼──┐     ┌───────▼──────────┐
  │PostgreSQL│     │ Appointment Svc  │
  └──────────┘     │ (HMS Connector)  │
                   └──────────────────┘
```

---

## 3. Detailed System Design

### 3.1 Call Session Design

Each phone call is represented as a **Call Session** object that persists the full state of the conversation.

```python
# Call Session State Structure
{
    "call_id": "uuid",
    "state": "active",                    # queued|ringing|active|ending|done
    "patient_id": "uuid",
    "appointment_id": "uuid",
    "script_id": "uuid",
    "current_node_id": "node-003",        # Current position in script flow
    "verified": false,                    # Identity verified?
    "verification_attempts": 0,
    "conversation_history": [
        {"speaker": "ai", "text": "Hello...", "ts": 0},
        {"speaker": "patient", "text": "Yes, hello", "ts": 3200}
    ],
    "entities": {
        "patient_name": "Priya Sharma",
        "appointment_date": "2025-03-10",
        "preferred_slot": null
    },
    "retry_count": 0,
    "sentiment_scores": [0.6, 0.7, 0.8],
    "escalation_requested": false,
    "started_at": "ISO8601",
    "last_activity": "ISO8601"
}
```

Session stored in **Redis** (TTL: 1 hour) for fast read/write during active call.

---

### 3.2 Script Flow Engine Design

Scripts are directed graphs (DAGs) stored as JSON:

```json
{
    "script_id": "scr-reminder-v1",
    "name": "Appointment Reminder v1",
    "nodes": [
        {
            "id": "node-001",
            "type": "speak",
            "text": "Hello! Am I speaking with {{patient_name}}?",
            "next": "node-002"
        },
        {
            "id": "node-002",
            "type": "listen",
            "timeout_ms": 5000,
            "intent_branch": {
                "patient_confirmed_identity": "node-003",
                "patient_denied": "node-end-wrong-person",
                "unclear": "node-002-retry"
            }
        },
        {
            "id": "node-003",
            "type": "api_call",
            "endpoint": "GET /appointments/{{appointment_id}}",
            "store_as": "appointment",
            "next": "node-004"
        },
        {
            "id": "node-004",
            "type": "speak",
            "text": "You have an appointment with Dr. {{appointment.doctor_name}} on {{appointment.date}} at {{appointment.time}}. Would you like to confirm?",
            "next": "node-005"
        },
        {
            "id": "node-005",
            "type": "listen",
            "intent_branch": {
                "confirm_appointment": "node-confirm",
                "reschedule_appointment": "node-reschedule",
                "cancel_appointment": "node-cancel",
                "request_human": "node-escalate"
            }
        },
        {
            "id": "node-confirm",
            "type": "api_call",
            "endpoint": "PATCH /appointments/{{appointment_id}}/status",
            "body": {"status": "confirmed"},
            "next": "node-confirm-speak"
        },
        {
            "id": "node-confirm-speak",
            "type": "speak",
            "text": "Your appointment is confirmed! You'll receive an SMS shortly. Goodbye!",
            "next": "node-end"
        },
        {
            "id": "node-end",
            "type": "end",
            "outcome": "appointment_confirmed",
            "trigger_sms": true
        }
    ]
}
```

---

### 3.3 Real-Time Audio Pipeline

```
Patient Voice
     ↓ (PCM audio, 8kHz, via WebSocket)
Twilio Media Streams
     ↓
Call Orchestrator receives audio chunks
     ↓
Google Cloud STT (streaming mode)
     ↓ (partial + final transcripts)
NLP Intent Classifier (Dialogflow CX)
     ↓ (intent + entities + confidence)
Script Engine (evaluate current node)
     ↓ (next response text)
Google WaveNet TTS
     ↓ (generated audio MP3/PCM)
Twilio plays audio to patient
```

**Latency Budget:**

| Step | Max Latency |
|---|---|
| Audio to STT partial | < 200ms |
| STT final transcript | < 500ms |
| NLP intent detection | < 150ms |
| Script step execution | < 50ms |
| TTS audio generation | < 200ms |
| Audio playback start | < 100ms |
| **Total E2E** | **< 1.2 seconds** |

---

### 3.4 Campaign Execution Design

```
Campaign Created
      ↓ (Admin triggers)
Campaign Service builds call queue:
    - Queries appointments matching filters
    - Checks DND for each patient
    - Creates campaign_call_queue records
      ↓
Kafka Topic: campaigns.queued
{
    "campaign_id": "uuid",
    "patient_id": "uuid",
    "appointment_id": "uuid",
    "scheduled_at": "ISO8601"
}
      ↓
Call Orchestrator Kafka Consumer Group
    - Multiple consumers (one per worker pod)
    - Each consumer picks one message at a time
    - Partition key = campaign_id (order per campaign)
      ↓
Call Orchestrator:
    1. Check if within call window (09:00–19:00)
    2. Check concurrent call limit
    3. Initiate Twilio call
    4. Publish call.initiated event
```

**Throttling**: Maximum 50 concurrent calls per campaign (configurable).

---

### 3.5 HMS Integration Design

The Appointment Service uses an **Adapter Pattern** to abstract HMS-specific APIs:

```python
class HMSAdapter(ABC):
    @abstractmethod
    async def get_appointment(self, appointment_id: str) -> Appointment:
        pass
    
    @abstractmethod
    async def update_appointment_status(self, id: str, status: str) -> bool:
        pass
    
    @abstractmethod
    async def get_available_slots(self, doctor_id: str, date: str) -> list[Slot]:
        pass

class MockHMSAdapter(HMSAdapter):
    """Used in development when real HMS is not available"""
    ...

class FHIRHMSAdapter(HMSAdapter):
    """HL7 FHIR R4 implementation"""
    ...

class CustomRestHMSAdapter(HMSAdapter):
    """Custom REST API for specific HMS vendors"""
    ...
```

---

### 3.6 Human Escalation Design

```
Patient triggers escalation
      ↓
Call Orchestrator:
1. Pauses script execution
2. Publishes escalation.requested event
3. Looks up available agent (round-robin)
      ↓ (no agent available)
TTS: "Please hold, connecting you to an agent..."
      ↓
Twilio Conference:
1. AI call → Conference Room
2. Agent's phone → Conference Room
3. Brief AI summary played to agent before joining
      ↓
Agent joins conference
AI leaves conference
      ↓
Agent handles rest of call
      ↓
Agent marks call resolved
Call record updated: outcome = "escalated_to_human"
```

**Agent Context Handoff Payload:**
```json
{
    "patient_name": "Priya Sharma",
    "phone": "+91-9876543210",
    "appointment": {
        "doctor": "Dr. Sunita Rao",
        "date": "March 10, 2025",
        "time": "10:30 AM"
    },
    "reason_for_call": "appointment_reminder",
    "last_patient_utterance": "I want to speak to someone about my insurance",
    "sentiment": "neutral",
    "transcript_url": "https://dashboard/calls/uuid/transcript"
}
```

---

## 4. Data Flow Diagrams

### 4.1 Appointment Confirmation Flow

```
[Campaign Scheduler] → Kafka: campaigns.queued
[Call Orchestrator Consumer] ← polls topic
    → DND check (Redis cache / TRAI API)
    → Twilio: initiate call
    → Redis: create call session
[Twilio] → patient phone rings
[Patient answers] → audio stream established
[STT] → "Yes, I'm Priya"
[NLP] → intent: patient_confirmed_identity (0.97)
[Script Engine] → move to node: present_appointment
[TTS] → "Your appointment is on March 10..."
[Patient] → "Yes, confirm"
[NLP] → intent: confirm_appointment (0.95)
[Appointment Service] → PATCH appointment status = confirmed
[HMS Adapter] → update HMS record
[Call ends]
[Kafka] → calls.completed event
[Notification Svc] → send SMS
[Scoring Engine] → compute quality score + sentiment
[Analytics Service] → increment campaign stats
[PostgreSQL] → persist final call record
```

---

## 5. Caching Strategy

| Data | Cache Key | TTL | Invalidation |
|---|---|---|---|
| Patient record by phone | `patient:phone:{phone}` | 30m | On patient update |
| Doctor availability | `slots:{doc_id}:{date}` | 15m | On slot booking |
| Campaign stats | `campaign:{id}:stats` | 1m | On each call complete |
| DND status | `dnd:{phone}` | 24h | Daily refresh |
| JWT blocklist | `jwt:blocked:{jti}` | Until expiry | On logout |
| Active call count | `calls:active:count` | Real-time | Increment/decrement |

---

## 6. Failure Handling & Resilience

### 6.1 Circuit Breaker Pattern (Twilio)
If Twilio fails > 5 calls in 60 seconds:
1. Circuit opens → switch to Exotel
2. Health check every 30 seconds
3. Circuit closes when 2 consecutive successes

### 6.2 Kafka Consumer Failure Recovery
- All messages have `retries` count in headers
- DLQ (Dead Letter Queue) after 3 retries
- DLQ monitored → alert to ops team

### 6.3 Call Mid-Drop Recovery
- STT sends periodic heartbeats
- If no audio for 5s → TTS: "Are you still there?"
- No response in 10s → graceful call end, status = `dropped`

### 6.4 HMS API Timeout
- Timeout: 3 seconds
- On timeout: TTS: "I'm having trouble checking your details. I'll have an agent call you."
- Call ends gracefully; queued for human follow-up

---

## 7. API Design Principles

| Principle | Implementation |
|---|---|
| Stateless APIs | No session in API; all state in DB/Redis |
| Idempotency | All POST endpoints support `Idempotency-Key` header |
| Pagination | Cursor-based for large datasets |
| Versioning | `/api/v1/` in URL |
| Consistent errors | RFC 7807 Problem Details format |
| OpenAPI 3.0 | Auto-generated from FastAPI annotations |

---

## 8. Deployment Architecture

```
                     Internet
                         │
                    [ CloudFlare ]
                    WAF + CDN
                         │
                  [ AWS ALB ]
                  Load Balancer
                         │
             ┌───────────┼───────────┐
             │           │           │
        [K8s Node 1] [K8s Node 2] [K8s Node 3]
             │           │           │
        ┌────────────────────────────────┐
        │          Kubernetes Cluster    │
        │  ┌──────────────────────────┐  │
        │  │ API Gateway (Kong)       │  │
        │  ├──────────────────────────┤  │
        │  │ Auth Service (2 pods)    │  │
        │  ├──────────────────────────┤  │
        │  │ Call Orchestrator (5+)   │  │ ← Scales dynamically
        │  ├──────────────────────────┤  │
        │  │ Appointment Service (3)  │  │
        │  ├──────────────────────────┤  │
        │  │ Notification Service (2) │  │
        │  ├──────────────────────────┤  │
        │  │ Analytics Service (2)    │  │
        │  └──────────────────────────┘  │
        └────────────────────────────────┘
             │           │           │
    ┌────────────┐ ┌────────┐ ┌──────────┐
    │ PostgreSQL │ │ Redis  │ │  Kafka   │
    │ Primary +  │ │Sentinel│ │ 3-Broker │
    │  Replica   │ │        │ │ Cluster  │
    └────────────┘ └────────┘ └──────────┘
```

---

## 9. Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Tool | Alert Threshold |
|---|---|---|
| Active call count | Prometheus | > 480 (approaching limit) |
| API error rate | Prometheus | > 2% in 5 min |
| Kafka consumer lag | Kafka UI | > 1000 messages |
| STT latency P95 | Prometheus | > 400ms |
| DB connection pool | Prometheus | > 80% utilized |
| Redis memory | Prometheus | > 85% |

### Alert Routing

| Severity | Channel | Response Time |
|---|---|---|
| P0 Critical | PagerDuty → On-call engineer | < 15 min |
| P1 High | Slack #alerts-critical | < 1 hour |
| P2 Medium | Slack #alerts-medium | < 4 hours |
| P3 Low | Jira ticket creation | Next business day |