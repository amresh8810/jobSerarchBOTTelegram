# Common Feature Enhancement Document
## AI Calling Agent — Hospital Appointment Booking System

---

## 1. Purpose

This document catalogs all common, cross-cutting features and enhancements that apply across the AI Calling Agent platform. These are not specific to one feature area but are foundational capabilities that improve the system holistically.

---

## 2. Feature Enhancement Categories

| Category | Description |
|---|---|
| **Accessibility** | Make platform usable for all users |
| **Localization** | Multi-language and regional support |
| **Theming** | UI branding and white-labeling |
| **Notifications** | Cross-feature notification system |
| **Performance** | System speed and efficiency gains |
| **Security** | Cross-cutting security hardening |
| **Audit & Compliance** | HIPAA / TRAI compliance helpers |
| **AI Improvements** | NLP/STT accuracy enhancements |

---

## 3. Detailed Feature Enhancements

### FE-01: Multilingual Support (Phase 2)

**Priority**: High  
**Effort**: 3 weeks

**Description**: Extend AI voice calls to support Hindi (hi-IN) as a primary language, with a framework for adding additional regional languages (Tamil, Bengali, Marathi) in Phase 3.

**Sub-features:**
- STT language model switched per patient's `language_pref` field
- TTS voice changed to Hindi neural voice (hi-IN-Wavenet-A)
- Dialogflow CX agent trained on Hindi intents
- Script translation system (admin uploads script in target language)
- Language auto-detection on call start (first 5 seconds)
- Admin dashboard localizable (i18n with React-i18next)

**Implementation Notes:**
```json
{
    "supported_languages": ["en-IN", "hi-IN"],
    "phase_3_languages": ["ta-IN", "bn-IN", "mr-IN"],
    "auto_detect_on_call": true,
    "fallback_language": "en-IN"
}
```

---

### FE-02: White-Label / Multi-Tenant Branding

**Priority**: Medium  
**Effort**: 2 weeks

**Description**: Allow each hospital client to customize the admin dashboard with their own branding (logo, colors, domain).

**Sub-features:**
- Per-tenant `settings.branding` JSON field in `hospitals` table
- Dynamic CSS variables for primary/secondary colors
- Custom logo upload (stored in S3 with CDN URL)
- Custom subdomain routing (e.g., `cityhosp.aicallagent.com`)
- White-labeled email/SMS templates (hospital name + logo in notifications)

**Branding Config Schema:**
```json
{
    "primary_color": "#0066CC",
    "secondary_color": "#004499",
    "logo_url": "https://cdn.hospital.com/logo.png",
    "favicon_url": "https://cdn.hospital.com/favicon.ico",
    "hospital_name_display": "City Hospital, Pune",
    "support_email": "support@cityhospital.com"
}
```

---

### FE-03: In-App Notification Center

**Priority**: High  
**Effort**: 1.5 weeks

**Description**: A persistent notification center in the dashboard (bell icon) showing real-time alerts and system events.

**Notification Types:**

| Type | Trigger | Priority |
|---|---|---|
| 🔴 Call Escalated | Patient requested human | Critical |
| 🟠 Campaign Failed | Campaign error | High |
| 🟡 Low Booking Rate | Booking rate < 50% | Medium |
| 🟢 Campaign Completed | Campaign finished | Info |
| 🔵 New Patient Import | CSV import done | Info |

**Technical Implementation:**
- New WebSocket channel `/ws/notifications`
- `notifications` table with `is_read` flag
- Badge count on bell icon (unread count)
- Click notification → navigate to relevant page

---

### FE-04: Advanced Search & Filtering

**Priority**: Medium  
**Effort**: 1 week

**Description**: Unified search experience across all entities (patients, calls, appointments).

**Features:**
- Global search bar in top navigation
- Search across: patients (name, phone, MRN), appointments, calls
- Instant results (debounced, 300ms)
- Recent searches history (stored in localStorage)
- Filter chips on list pages (stackable, clearable)
- Saved filter presets

**Search API:**
```
GET /api/v1/search?q={query}&types=patients,appointments,calls&limit=10
```

---

### FE-05: Keyboard Shortcuts & Accessibility

**Priority**: Medium  
**Effort**: 1 week

**Standards**: WCAG 2.1 AA compliance

**Keyboard Shortcuts:**

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl + K` | Open global search |
| `Cmd/Ctrl + N` | Create new (context-aware) |
| `G + D` | Go to Dashboard |
| `G + C` | Go to Calls |
| `G + A` | Go to Appointments |
| `Esc` | Close modal / panel |

**Accessibility Enhancements:**
- All interactive elements have ARIA labels
- Focus trapping in modals
- Sufficient color contrast (4.5:1 minimum)
- Screen reader optimized table headers
- Loading state announcements for screen readers

---

### FE-06: Audit Trail Viewer

**Priority**: High (HIPAA compliance)  
**Effort**: 1 week

**Description**: Admin can view a complete audit trail of all actions taken in the system.

**Filter Options:**
- By user, by entity type, by date range, by action

**Display:**
```
[2025-03-09 09:32:14] admin@hospital.com | CANCELLED | appointment apt-uuid
    Old: { status: "scheduled" }
    New: { status: "cancelled", reason: "patient request" }
    IP: 192.168.1.45 | User Agent: Chrome/120
```

**Compliance Notes:**
- Logs immutable (no DELETE allowed)
- Stored for 2 years minimum
- Exportable as CSV for compliance audits

---

### FE-07: Role-Based Dashboard Views

**Priority**: High  
**Effort**: 1 week

**Description**: Dashboard content and navigation adapts based on user role.

| Role | Default View | Permissions |
|---|---|---|
| **Admin** | Full dashboard, all sections | Full CRUD on all entities |
| **Supervisor** | Live calls, escalation queue | View + escalation management |
| **Agent** | Escalation queue, patient lookup | Limited view of assigned cases |
| **Doctor** | Own appointment schedule | Read-only on own appointments |
| **Analyst** | Analytics + reports only | Read-only analytics |

---

### FE-08: Export & Reporting Enhancements

**Priority**: Medium  
**Effort**: 1.5 weeks

**Export Formats Supported:**

| Format | Use Case |
|---|---|
| CSV | Raw data export for analysis |
| PDF | Formatted reports for management |
| Excel (XLSX) | Detailed data with pivot table support |

**Scheduled Reports:**
- Admin can schedule weekly/monthly reports
- Reports emailed automatically to defined recipients
- Report types: Call Summary, Campaign Results, No-Show Analysis

---

### FE-09: Dark Mode Support

**Priority**: Low  
**Effort**: 0.5 weeks

**Description**: Full dark mode support for the admin dashboard.

**Implementation:**
- CSS variables for all colors (`--color-bg`, `--color-text`, etc.)
- Toggle in user settings (preference saved to DB)
- Respects OS-level `prefers-color-scheme`
- All charts and icons also adapt

---

### FE-10: Performance Optimizations

**Priority**: High (ongoing)  
**Effort**: Continuous

| Optimization | Technique | Expected Improvement |
|---|---|---|
| API response caching | Redis with 15min TTL | 70% reduction in DB queries |
| Dashboard lazy loading | React.lazy + Suspense | 40% faster initial load |
| Table virtualization | react-virtual | Render 10K rows smoothly |
| Image optimization | Next-gen formats (WebP, AVIF) | 60% smaller image sizes |
| Code splitting | Vite chunk splitting | 50% smaller initial JS bundle |
| WebSocket reconnect | Exponential backoff | No manual refresh needed |

---

## 4. Technical Debt & Refactoring Items

| Item | Description | Priority |
|---|---|---|
| TD-01 | Standardize error handling across all services | High |
| TD-02 | Extract common API client into shared package | Medium |
| TD-03 | Replace polling with WebSocket for live calls | High |
| TD-04 | Add OpenAPI spec generation (automated) | Medium |
| TD-05 | Migrate remaining hardcoded configs to env | High |
| TD-06 | Add connection pooling for HMS API calls | Medium |

---

## 5. Feature Flag System

All new features are released behind feature flags for controlled rollout.

**Implementation**: LaunchDarkly / custom Redis-based flags

**Usage:**
```typescript
// Frontend
const { isEnabled } = useFeatureFlag('hindi-language-support');

// Backend (Python)
if feature_flags.is_enabled("hindi-language-support", hospital_id):
    use_hindi_tts()
```

**Active Feature Flags:**

| Flag Name | Default | Description |
|---|---|---|
| `hindi-language-support` | OFF | Enable hi-IN language for calls |
| `sentiment-analysis` | ON | Show sentiment score in dashboard |
| `no-show-risk-score` | OFF | Show risk badge on appointments |
| `whatsapp-integration` | OFF | Send WhatsApp follow-ups |
| `dark-mode` | ON | Allow dark mode toggle |
