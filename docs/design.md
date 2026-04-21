# Activity Registration and Funding Audit Management Platform — System Design

---

## 1. Overview

### What the System Does

The Activity Registration and Funding Audit Management Platform is an integrated closed-loop management system that handles the full lifecycle of activity registrations — from applicant submission through review, funding audit, and compliance reporting. It serves four distinct user roles: **Applicants**, **Reviewers**, **Financial Administrators**, and **System Administrators**.

### Key Goals

| Goal | Description |
|---|---|
| **Closed-loop management** | Every registration flows through a traceable state machine from submission to final disposition |
| **Material integrity** | File uploads are validated, versioned (max 3), fingerprinted (SHA-256), and locked after deadlines |
| **Funding accountability** | Income/expense tracking with 10% overspend warnings and audit trails |
| **Offline-first** | All data in PostgreSQL, all files on local disk — zero external service dependencies |
| **Security & compliance** | Strong password hashing, role-based masking, brute-force protection, access auditing, daily backups |
| **Auditability** | Every review action, financial transaction, and access event is logged with traceable records |

---

## 2. Architecture

### Type: Modular Monolith

The system is a **modular monolith** with clear domain separation. A single FastAPI application serves RESTful APIs, with Vue.js on the frontend.

### High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Vue.js Frontend                          │
│  Form Wizard │ Review Dashboard │ Finance Panel │ Admin UI   │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS / REST
┌──────────────────────▼───────────────────────────────────────┐
│                     FastAPI Backend                           │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐            │
│  │    Auth     │  │ Registration│  │   Review    │            │
│  │   Module    │  │   Module   │  │   Module    │            │
│  └────────────┘  └────────────┘  └─────────────┘            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐            │
│  │  Material   │  │  Funding   │  │  Reporting  │            │
│  │   Module    │  │   Module   │  │   Module    │            │
│  └────────────┘  └────────────┘  └─────────────┘            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐            │
│  │   Quality   │  │  Data      │  │   Backup    │            │
│  │  Metrics    │  │ Collection │  │   Module    │            │
│  └────────────┘  └────────────┘  └─────────────┘            │
│                                                              │
│  ┌─────────────────────────────────────────────┐             │
│  │        Cross-cutting: Middleware Layer       │             │
│  │  Auth Guard │ Rate Limiter │ Audit Logger    │             │
│  └─────────────────────────────────────────────┘             │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │      PostgreSQL         │
          │  (all persistent data)  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Local Disk Storage   │
          │  (uploaded files, backups)│
          └─────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| **Auth Module** | User registration, login, logout, JWT token management, brute-force protection, password hashing |
| **Registration Module** | Registration form CRUD, form wizard state, field validation, deadline management |
| **Material Module** | File upload/download, type/size validation, versioning (max 3, FIFO eviction), SHA-256 fingerprinting, deadline locking, supplementary submissions |
| **Review Module** | State machine workflow, batch review, review comments, traceable logs, waitlist management |
| **Funding Module** | Funding accounts, income/expense transactions, invoice attachments, budget overspend detection, category/time statistics |
| **Reporting Module** | Quality metrics (approval/correction/overspending rates), reconciliation/audit/compliance reports, data export |
| **Quality Metrics** | Compute approval rate, correction rate, overspending rate; trigger local alerts on threshold violations |
| **Data Collection Module** | Data collection batches, quality validation results, whitelist policies |
| **Backup Module** | Daily local backups, one-click recovery |
| **Middleware Layer** | Authentication guard, rate limiting (brute-force), request/response audit logging, role-based access control |

---

## 3. Data Model

### Entity Relationship Overview

```
User 1──N Registration
Registration 1──N MaterialChecklist
MaterialChecklist 1──N MaterialVersion
Registration 1──N ReviewRecord
Registration 1──1 FundingAccount
FundingAccount 1──N TransactionRecord
User 1──N AuditLog
DataCollectionBatch 1──N QualityValidationResult
```

### Entities

#### User

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | NOT NULL (bcrypt/argon2) |
| `salt` | VARCHAR(64) | NOT NULL |
| `role` | ENUM | `applicant`, `reviewer`, `financial_admin`, `system_admin` |
| `id_number` | VARCHAR(50) | Encrypted at rest, role-masked on read |
| `contact_info` | VARCHAR(255) | Encrypted at rest, role-masked on read |
| `is_locked` | BOOLEAN | Default: false |
| `locked_until` | TIMESTAMP | Nullable |
| `failed_login_attempts` | INTEGER | Default: 0 |
| `first_failed_at` | TIMESTAMP | Nullable |
| `created_at` | TIMESTAMP | NOT NULL |
| `updated_at` | TIMESTAMP | NOT NULL |

#### Registration

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `applicant_id` | UUID | FK → User, NOT NULL |
| `activity_id` | UUID | FK → Activity, NOT NULL |
| `form_data` | JSONB | Form wizard fields |
| `requested_funding` | DECIMAL(12,2) | NOT NULL, > 0; locked after approval |
| `status` | ENUM | `draft`, `submitted`, `supplemented`, `approved`, `rejected`, `canceled`, `waitlisted` |
| `deadline` | TIMESTAMP | NOT NULL |
| `is_locked` | BOOLEAN | Default: false (auto-set after deadline) |
| `supplementary_requested_at` | TIMESTAMP | Nullable; set when reviewer marks "Needs Correction" |
| `supplementary_deadline` | TIMESTAMP | Computed: `supplementary_requested_at + 72h` |
| `supplementary_used` | BOOLEAN | Default: false |
| `created_at` | TIMESTAMP | NOT NULL |
| `updated_at` | TIMESTAMP | NOT NULL |

#### Activity

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR(255) | NOT NULL |
| `description` | TEXT | Nullable |
| `deadline` | TIMESTAMP | NOT NULL |
| `budget` | DECIMAL(14,2) | NOT NULL, > 0 |
| `is_active` | BOOLEAN | Default: true |
| `created_at` | TIMESTAMP | NOT NULL |
| `updated_at` | TIMESTAMP | NOT NULL |

#### MaterialChecklist

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `registration_id` | UUID | FK → Registration, NOT NULL |
| `item_name` | VARCHAR(255) | NOT NULL |
| `is_required` | BOOLEAN | Default: true |
| `allowed_types` | VARCHAR(100)[] | e.g., `["pdf","jpg","png"]` |
| `max_file_size_mb` | INTEGER | Default: 20 |
| `created_at` | TIMESTAMP | NOT NULL |

#### MaterialVersion

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `checklist_item_id` | UUID | FK → MaterialChecklist, NOT NULL |
| `version_number` | INTEGER | 1–3 |
| `file_path` | VARCHAR(500) | Local disk path |
| `file_name` | VARCHAR(255) | Original upload name |
| `file_size_bytes` | BIGINT | NOT NULL |
| `file_type` | VARCHAR(20) | NOT NULL |
| `sha256_hash` | VARCHAR(64) | NOT NULL, system-wide unique check |
| `label` | ENUM | `pending_submission`, `submitted`, `needs_correction` |
| `uploaded_at` | TIMESTAMP | NOT NULL |
| `uploaded_by` | UUID | FK → User |

#### ReviewRecord

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `registration_id` | UUID | FK → Registration, NOT NULL |
| `reviewer_id` | UUID | FK → User (role=reviewer), NOT NULL |
| `previous_status` | ENUM | Status before transition |
| `new_status` | ENUM | Status after transition |
| `comment` | TEXT | Nullable |
| `correction_reason` | TEXT | Required when `new_status = needs_correction` |
| `batch_id` | UUID | Nullable; set for batch reviews |
| `created_at` | TIMESTAMP | NOT NULL |

#### FundingAccount

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `registration_id` | UUID | FK → Registration, UNIQUE, NOT NULL |
| `approved_budget` | DECIMAL(12,2) | = `registration.requested_funding` at approval |
| `total_income` | DECIMAL(12,2) | Computed / cached |
| `total_expenses` | DECIMAL(12,2) | Computed / cached |
| `created_at` | TIMESTAMP | NOT NULL |
| `updated_at` | TIMESTAMP | NOT NULL |

#### TransactionRecord

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `funding_account_id` | UUID | FK → FundingAccount, NOT NULL |
| `type` | ENUM | `income`, `expense` |
| `amount` | DECIMAL(12,2) | NOT NULL, > 0 |
| `category` | VARCHAR(100) | NOT NULL |
| `description` | TEXT | Nullable |
| `invoice_file_path` | VARCHAR(500) | Nullable (for expenses with invoices) |
| `recorded_by` | UUID | FK → User (role=financial_admin) |
| `created_at` | TIMESTAMP | NOT NULL |

#### AuditLog

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK → User, Nullable (system actions) |
| `action` | VARCHAR(100) | NOT NULL (e.g., `login`, `review`, `upload`, `transaction`) |
| `resource_type` | VARCHAR(100) | Entity type affected |
| `resource_id` | UUID | Entity ID affected |
| `details` | JSONB | Additional context |
| `ip_address` | VARCHAR(45) | NOT NULL |
| `created_at` | TIMESTAMP | NOT NULL |

#### DataCollectionBatch

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `name` | VARCHAR(255) | NOT NULL |
| `scope_whitelist` | JSONB | Defines allowed data scope |
| `status` | ENUM | `pending`, `in_progress`, `completed`, `failed` |
| `created_by` | UUID | FK → User |
| `created_at` | TIMESTAMP | NOT NULL |
| `completed_at` | TIMESTAMP | Nullable |

#### QualityValidationResult

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `batch_id` | UUID | FK → DataCollectionBatch, NOT NULL |
| `registration_id` | UUID | FK → Registration, NOT NULL |
| `validation_type` | VARCHAR(100) | e.g., `type_check`, `range_check`, `mandatory_check` |
| `is_valid` | BOOLEAN | NOT NULL |
| `error_details` | TEXT | Nullable |
| `created_at` | TIMESTAMP | NOT NULL |

#### AlertRecord

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `alert_type` | VARCHAR(100) | e.g., `overspend_warning`, `threshold_exceeded` |
| `severity` | ENUM | `info`, `warning`, `critical` |
| `message` | TEXT | NOT NULL |
| `resource_type` | VARCHAR(100) | Related entity type |
| `resource_id` | UUID | Related entity ID |
| `acknowledged` | BOOLEAN | Default: false |
| `acknowledged_by` | UUID | FK → User, Nullable |
| `created_at` | TIMESTAMP | NOT NULL |

#### BackupRecord

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK |
| `backup_path` | VARCHAR(500) | NOT NULL |
| `backup_type` | ENUM | `daily_auto`, `manual` |
| `size_bytes` | BIGINT | NOT NULL |
| `status` | ENUM | `completed`, `failed` |
| `created_at` | TIMESTAMP | NOT NULL |
| `restored_at` | TIMESTAMP | Nullable |

---

## 4. Core Flows

### Flow 1: Registration Submission

```
Applicant opens form wizard
  → Fills form fields (step-by-step)
  → For each checklist item:
      → Uploads file
      → Backend validates: type ∈ {PDF, JPG, PNG}, size ≤ 20MB, total ≤ 200MB
      → Backend computes SHA-256 → checks system-wide duplicates
      → If version count = 3 → FIFO eviction (delete oldest, save new)
      → Saves file to local disk, records in MaterialVersion
  → Submits registration
  → Status transitions: draft → submitted
  → Audit log recorded
```

### Flow 2: Post-Deadline Supplementary Submission

```
Reviewer marks registration as "Needs Correction"
  → System records supplementary_requested_at = NOW()
  → 72-hour countdown begins
  → Applicant sees time-remaining clock
  → Within 72h: applicant uploads corrected materials
      → Same validation rules apply
      → supplementary_used = true
      → Status: submitted → supplemented
  → After 72h: supplementary window closes, materials locked
  → One-time only: if supplementary_used = true, no further supplements allowed
```

### Flow 3: Review Workflow (State Machine)

```
                    ┌──────────┐
                    │  Draft   │
                    └────┬─────┘
                         │ submit
                    ┌────▼─────┐
             ┌──────│ Submitted│──────┐
             │      └────┬─────┘      │
             │           │            │
        supplement       │         cancel
             │      ┌────▼─────┐      │
             │      │ Needs    │      │
             ├──────│Correction│      │
             │      └────┬─────┘      │
             │           │            │
        ┌────▼──────┐    │       ┌────▼────┐
        │Supplemented│   │       │Canceled │
        └────┬──────┘    │       └─────────┘
             │           │
             └─────┬─────┘
                   │ approve / reject / waitlist
           ┌───────┼───────┐
      ┌────▼──┐ ┌──▼───┐ ┌─▼────────┐
      │Approved│ │Reject│ │Waitlisted│
      └───────┘ └──────┘ └────┬─────┘
                               │ manual promote
                          ┌────▼──┐
                          │Approved│
                          └───────┘

Batch review: ≤ 50 registrations per batch
Each transition → ReviewRecord created → AuditLog created
```

### Flow 4: Financial Management

```
Financial Admin opens approved registration
  → Views / creates FundingAccount (auto-created on approval)
  → Records income or expense:
      → Type, amount, category, description
      → Optional: upload invoice attachment
  → On each expense record:
      → System computes total_expenses
      → If total_expenses > approved_budget * 1.10:
          → Returns overspend_warning flag in response
          → Frontend shows popup requiring secondary confirmation
          → If confirmed → transaction saved with override flag
          → AlertRecord created
  → Generate statistics by category and time period
```

### Flow 5: Quality Metrics & Alerts

```
System computes (on-demand or scheduled):
  → Approval rate = approved / total_reviewed
  → Correction rate = needs_correction / total_reviewed
  → Overspending rate = overspent_accounts / total_accounts
  → If any metric exceeds configured threshold:
      → AlertRecord created
      → Alert surfaced to system admin dashboard
```

### Flow 6: Authentication & Brute-Force Protection

```
User submits login (username + password)
  → Check if account is locked:
      → If locked_until > NOW(): reject with 423 Locked
  → Verify password hash:
      → If failed:
          → Increment failed_login_attempts
          → If first failure: set first_failed_at = NOW()
          → If failed_login_attempts ≥ 10 AND NOW() - first_failed_at ≤ 5 min:
              → Set is_locked = true, locked_until = NOW() + 30 min
              → Return 423 Locked
      → If success:
          → Reset failed_login_attempts, first_failed_at
          → Issue JWT access token
          → Record AuditLog (login)
```

### Flow 7: Backup & Recovery

```
Daily (automated):
  → pg_dump PostgreSQL database
  → Archive uploaded files
  → Save to configured backup directory
  → Record BackupRecord

One-click recovery:
  → Admin selects backup from list
  → System restores database + files
  → Records restoration in AuditLog
```

---

## 5. Business Logic

### Registration Rules

- Form wizard fields validated against checklist configuration (type, range, mandatory consistency)
- `requested_funding` must be > 0 and is locked (immutable) once status = `approved`
- Registration is auto-locked when `deadline` passes — no further edits except supplementary
- Supplementary submission: one-time only, 72-hour window from reviewer's "Needs Correction" timestamp

### Material Rules

- Allowed file types: PDF, JPG, PNG (configurable per checklist item)
- Single file size: ≤ 20MB
- Total upload size per registration: ≤ 200MB
- Maximum 3 versions per checklist item; 4th upload triggers FIFO eviction (oldest deleted)
- SHA-256 duplicate detection: system-wide scope — upload rejected if hash exists anywhere
- Materials locked after deadline (except during active supplementary window)
- Version labels: `pending_submission`, `submitted`, `needs_correction`

### Review Rules

- State machine transitions: only valid paths allowed (see Flow 3)
- Batch review: maximum 50 registrations per operation
- Waitlist promotion: manual reviewer action (not automatic)
- Every transition creates a ReviewRecord with comment + timestamp
- Correction reason required when transitioning to "Needs Correction"

### Funding Rules

- FundingAccount auto-created when registration is approved
- `approved_budget` = `registration.requested_funding` (locked at approval)
- Overspend threshold: `total_expenses > approved_budget × 1.10`
- Overspend requires secondary confirmation (frontend popup + API confirmation flag)
- Invoice attachments stored on local disk with same validation rules as materials

### Security Rules

- Passwords: bcrypt or argon2 hashing with unique salt per user
- Brute-force: ≥ 10 failed attempts in 5 minutes → account locked 30 minutes
- Sensitive fields (ID numbers, contact info): role-based masking
  - Financial Admin: sees `****`
  - Reviewer: full data accessible via "Verify" action (logged in audit trail)
  - Applicant: sees own data unmasked
  - System Admin: full access
- All API access audited in AuditLog
- Sensitive configuration values encrypted at rest

---

## 6. API Design Strategy

### REST Conventions

- **Base URL**: `/api/v1`
- **Resource naming**: lowercase, plural nouns (e.g., `/registrations`, `/materials`)
- **HTTP methods**: GET (read), POST (create), PUT (full update), PATCH (partial update / state transitions), DELETE (remove)
- **Nested resources**: for strong ownership (e.g., `/registrations/{id}/materials`)
- **Query parameters**: for filtering, pagination, sorting (e.g., `?page=1&per_page=20&sort=-created_at`)

### Versioning

- URL-based versioning: `/api/v1/...`
- Breaking changes increment version (v2, v3, etc.)

### Naming Conventions

| Pattern | Example |
|---|---|
| List resources | `GET /api/v1/registrations` |
| Get single | `GET /api/v1/registrations/{id}` |
| Create | `POST /api/v1/registrations` |
| Update | `PUT /api/v1/registrations/{id}` |
| State transition | `PATCH /api/v1/registrations/{id}/transition` |
| Nested resource | `GET /api/v1/registrations/{id}/materials` |
| Action endpoint | `POST /api/v1/reviews/batch` |

### Pagination

All list endpoints return paginated responses:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

---

## 7. Authentication & Authorization

### Authentication

- **Method**: Username + Password → JWT Bearer Token
- **Token type**: JWT (access token)
- **Token lifetime**: Configurable (default: 24 hours)
- **Header**: `Authorization: Bearer <token>`
- **Public endpoints**: `POST /auth/login`, `POST /auth/register` (system admin only)

### Authorization (Role-Based Access Control)

| Role | Permissions |
|---|---|
| `applicant` | Create/view own registrations, upload/view own materials, view own funding account |
| `reviewer` | View all registrations, perform reviews, batch review, manage waitlist, verify sensitive data |
| `financial_admin` | View approved registrations, manage funding accounts/transactions, upload invoices, view statistics |
| `system_admin` | Full access: user management, activity management, system configuration, backups, reports, alerts |

### Object-Level Authorization

- Applicants can only access their own registrations and materials
- Financial admins can only manage funding for approved registrations
- Reviewers can access all registrations but only for review actions
- All sensitive data access is logged

---

## 8. Validation Rules

### Registration Validation

| Field | Rule |
|---|---|
| `applicant_id` | Must be valid, existing applicant user |
| `activity_id` | Must be valid, active activity |
| `requested_funding` | Required, numeric, > 0 |
| `form_data` | Validated against activity's checklist schema (type, range, mandatory) |
| `deadline` | Must be future date when creating |

### Material Upload Validation

| Rule | Constraint |
|---|---|
| File type | Must be in checklist item's `allowed_types` (default: PDF, JPG, PNG) |
| Single file size | ≤ 20MB (20,971,520 bytes) |
| Total per registration | ≤ 200MB (209,715,200 bytes) |
| SHA-256 hash | Must not match any existing hash in the system |
| Version count | Max 3; 4th triggers FIFO eviction |
| Deadline | Upload rejected after deadline (unless in supplementary window) |

### Review Validation

| Rule | Constraint |
|---|---|
| State transition | Must follow valid state machine paths |
| Batch size | ≤ 50 registrations per batch operation |
| Correction reason | Required when transitioning to "Needs Correction" |
| Reviewer role | Only users with `reviewer` role can perform reviews |

### Financial Validation

| Rule | Constraint |
|---|---|
| Amount | Required, numeric, > 0 |
| Category | Required, non-empty string |
| Overspend check | If `total_expenses > approved_budget * 1.10`, require `override_confirmed = true` |

### Authentication Validation

| Rule | Constraint |
|---|---|
| Username | Required, 3–100 characters, alphanumeric + underscore |
| Password | Required, ≥ 8 characters, must contain uppercase, lowercase, digit, special character |
| Brute-force | ≥ 10 failures in 5 min → 30-min lock |

---

## 9. Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human-readable message"
  }
}
```

### Error Code Registry

| HTTP Status | Code | Usage |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request body/params failed validation |
| 400 | `INVALID_STATE_TRANSITION` | State machine violation |
| 400 | `DUPLICATE_FILE` | SHA-256 hash already exists |
| 400 | `FILE_TYPE_NOT_ALLOWED` | Upload type not in allowed list |
| 400 | `FILE_TOO_LARGE` | Single file > 20MB or total > 200MB |
| 400 | `DEADLINE_PASSED` | Registration/material deadline exceeded |
| 400 | `SUPPLEMENTARY_EXHAUSTED` | One-time supplementary already used |
| 400 | `SUPPLEMENTARY_EXPIRED` | 72-hour supplementary window closed |
| 400 | `BATCH_SIZE_EXCEEDED` | Batch review > 50 items |
| 400 | `BUDGET_LOCKED` | Attempted to modify locked budget |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Insufficient role/permission |
| 403 | `OVERSPEND_CONFIRMATION_REQUIRED` | Expense exceeds 110% budget, needs confirmation |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource state conflict |
| 423 | `ACCOUNT_LOCKED` | Brute-force lockout active |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## 10. Assumptions & Decisions

### From questions.md

**Q1: Waitlist Promotion Trigger**
- **Question**: Does the system automatically "Promote from Waitlist" when an Approved slot opens, or is it a manual Reviewer action?
- **Decision**: Manual promotion. "Waitlisted" is a status a Reviewer can assign. Promotion to "Approved" is performed via a manual action on the reviewer's dashboard.
- **Reasoning**: The state machine lists it as a state but defines no automatic trigger. Manual control gives reviewers oversight and avoids unintended approvals.

**Q2: Material Versioning Eviction**
- **Question**: When a user uploads a 4th version of a document, how does the system handle the "up to three versions" limit?
- **Decision**: FIFO eviction. The oldest version (version 1) is deleted from disk and database; the new file becomes the latest version.
- **Reasoning**: "Retaining up to three versions" implies a rolling window. FIFO provides predictable behavior and conserves storage.

**Q3: Supplementary Window Activation**
- **Question**: Does the 72-hour timer start from the Activity Deadline or the Reviewer's "Needs Correction" action?
- **Decision**: Timer starts from the Reviewer's "Needs Correction" action timestamp (`supplementary_requested_at`).
- **Reasoning**: The supplementary process is a correction feedback loop, not tied to the original deadline. Starting from reviewer action ensures applicants get the full 72 hours for corrections.

**Q4: Budget Baseline Source**
- **Question**: Which field serves as the baseline for the "10% overspend" warning?
- **Decision**: The `requested_funding` field in the Registration model, locked at approval time and copied to `FundingAccount.approved_budget`.
- **Reasoning**: The approved funding amount is the contractual baseline. Locking it prevents post-approval manipulation.

**Q5: Identity Masking vs. Reviewer Access**
- **Question**: If ID numbers are masked, how can Reviewers perform quality validation against uploaded ID materials?
- **Decision**: Role-based masking with reveal capability. Financial Admins see `****`. Reviewers see masked data by default but can click "Verify" to reveal the full data. This reveal action is recorded in audit logs.
- **Reasoning**: Separation of duties — reviewers need to verify identity for quality control, but access is logged for accountability.

**Q6: Duplicate Detection Scope**
- **Question**: Does the SHA-256 duplicate check look for duplicates within a single application or across the entire system?
- **Decision**: System-wide scope. The SHA-256 fingerprint is checked against all files in the materials table.
- **Reasoning**: Cross-application duplicate detection prevents the same document being submitted across different applications to claim the same funding, which is the primary fraud prevention use case.

### Additional Assumptions

- **JWT tokens** are used (not session-based auth) for stateless API access
- **User registration** is restricted to system administrators (no self-registration for security)
- **Activities** are managed by system administrators and define the context for registrations
- **Similarity/duplicate check** interface exists but is disabled by default (reserved endpoint, returns 501)
- **Daily backups** run via a scheduled task (cron or equivalent)
- **File storage paths** are configurable via environment variables
- **All timestamps** are stored in UTC

---

## 11. Scalability & Extensibility

### Current Scale Design

- Single PostgreSQL instance handles all queries
- Local file storage with configurable base path
- Synchronous request processing (sufficient for offline deployment)

### Extension Points

| Area | Extension Path |
|---|---|
| **File storage** | Abstract storage interface → swap local disk for S3-compatible storage |
| **Similarity check** | Reserved endpoint ready for ML/NLP integration when needed |
| **Notifications** | AuditLog + AlertRecord infrastructure supports future email/push notifications |
| **Multi-tenancy** | Activity-based isolation already in place; can add organization layer |
| **Reporting** | JSONB fields and flexible query patterns support future custom report builders |
| **Authentication** | JWT infrastructure supports future OAuth2/OIDC integration |
| **Batch processing** | DataCollectionBatch entity supports future async job processing |
