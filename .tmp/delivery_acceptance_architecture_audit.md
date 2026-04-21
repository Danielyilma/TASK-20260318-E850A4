# Delivery Acceptance and Project Architecture Audit (Static)

## 1. Verdict
- Overall conclusion: **Fail**

## 2. Scope and Static Verification Boundary
- Reviewed scope: `repo/` backend/frontend source, API/docs artifacts, migrations, tests, and top-level docs (`docs/`, `prompt.md`, `implementation/`).
- Not reviewed: runtime behavior in live server/browser sessions, Docker runtime execution, external integrations, OS-level schedulers.
- Intentionally not executed: project startup, Docker, tests, background tasks, restore/backup commands.
- Manual verification required for: actual runtime startup, browser rendering/interactions, pg_dump/psql execution in target environment, scheduled daily backup automation.

## 3. Repository / Requirement Mapping Summary
- Prompt core mapped: applicant wizard + materials/versioning, reviewer workflow + batch review, financial accounting + overspend confirmation, FastAPI + PostgreSQL + local file storage + SHA-256 duplicate checks, audit/metrics/reports/backups/security controls.
- Main implementation areas reviewed: backend route registry and endpoint modules, models/schemas/migrations, auth/security middleware, frontend routes/stores/views, and backend/frontend tests.
- Result: substantial feature surface exists, but multiple hard-gate and security/business-integrity defects remain.

## 4. Section-by-section Review

### 1. Hard Gates

#### 1.1 Documentation and static verifiability
- Conclusion: **Fail**
- Rationale: documented startup/config is statically inconsistent with required runtime config; API docs diverge materially from implemented routes/shapes.
- Evidence: `repo/backend/app/core/config.py:11`, `repo/backend/app/core/config.py:15`, `repo/README.md:45`, `repo/README.md:52`, `repo/README.md:71`, `repo/README.md:74`, `repo/docker-compose.yml:29`, `repo/docker-compose.yml:33`, `repo/README.md:124`, `docs/api-spec.md:974`, `repo/backend/app/api/v1/endpoints/materials.py:407`, `docs/api-spec.md:2211`, `repo/backend/app/api/v1/endpoints/materials.py:37`, `docs/api-spec.md:238`, `docs/api-spec.md:267`, `repo/backend/app/api/v1/endpoints/users.py:40`, `repo/backend/app/api/v1/endpoints/users.py:49`
- Manual verification note: N/A (static defects).

#### 1.2 Whether delivery materially deviates from Prompt
- Conclusion: **Partial Pass**
- Rationale: implementation broadly targets the requested platform, but key deviations exist in deadline enforcement, backup correctness, and least-privilege scope.
- Evidence: `repo/backend/app/api/v1/endpoints/registrations.py:65`, `repo/backend/app/api/v1/endpoints/registrations.py:70`, `repo/backend/app/api/v1/endpoints/registrations.py:148`, `repo/backend/app/api/v1/endpoints/registrations.py:198`, `repo/backend/app/api/v1/endpoints/backups.py:68`, `repo/backend/app/api/v1/endpoints/backups.py:73`, `repo/backend/app/api/v1/endpoints/materials.py:192`, `repo/backend/app/api/v1/endpoints/registrations.py:108`, `repo/backend/app/api/v1/endpoints/registrations.py:111`, `prompt.md:5`, `prompt.md:7`
- Manual verification note: N/A.

### 2. Delivery Completeness

#### 2.1 Core requirement coverage
- Conclusion: **Partial Pass**
- Rationale: most core modules exist (registration/materials/review/funding/metrics/reports/backups/data collection), but several explicit requirements are incomplete or inconsistent.
- Evidence: `repo/backend/app/api/v1/api.py:10`, `repo/backend/app/api/v1/api.py:22`, `repo/backend/app/api/v1/endpoints/reviews.py:22`, `repo/backend/app/api/v1/endpoints/funding.py:98`, `repo/backend/app/api/v1/endpoints/funding.py:465`, `repo/backend/app/api/v1/endpoints/data_collection.py:61`, `repo/backend/app/api/v1/endpoints/data_collection.py:104`, `repo/frontend/src/views/RegistrationWizard.vue:53`, `repo/frontend/src/views/RegistrationWizard.vue:179`, `repo/frontend/src/views/FinancialDashboard.vue:168`, `repo/frontend/src/views/FinancialDashboard.vue:190`
- Manual verification note: UI behavior quality and runtime orchestration require browser/API runtime checks.

#### 2.2 Basic end-to-end deliverable (0→1)
- Conclusion: **Fail**
- Rationale: first-run bootstrap path is missing (no documented/admin seed path), and required config is incomplete in setup docs.
- Evidence: `repo/backend/app/api/v1/endpoints/auth.py:20`, `repo/backend/app/api/v1/endpoints/users.py:16`, `repo/README.md:64`, `repo/README.md:82`, `repo/backend/app/core/config.py:11`
- Manual verification note: N/A.

### 3. Engineering and Architecture Quality

#### 3.1 Engineering structure and module decomposition
- Conclusion: **Pass**
- Rationale: modular backend endpoint/model/schema decomposition and frontend store/view/router separation are present; not a single-file implementation.
- Evidence: `repo/backend/app/api/v1/api.py:2`, `repo/backend/app/models/registration.py:7`, `repo/backend/app/models/material.py:7`, `repo/backend/app/models/funding.py:7`, `repo/frontend/src/router/index.js:5`, `repo/frontend/src/stores/registration.store.js:4`, `repo/frontend/src/views/SystemAdmin.vue:1`
- Manual verification note: N/A.

#### 3.2 Maintainability and extensibility
- Conclusion: **Partial Pass**
- Rationale: structure is maintainable, but heavy business logic in endpoints, drift between docs/contracts and code, and fragile backup/data-collection implementations reduce extensibility confidence.
- Evidence: `repo/backend/app/api/v1/endpoints/registrations.py:18`, `repo/backend/app/api/v1/endpoints/backups.py:36`, `repo/backend/app/api/v1/endpoints/data_collection.py:61`, `docs/api-spec.md:970`, `repo/backend/app/api/v1/endpoints/materials.py:407`
- Manual verification note: N/A.

### 4. Engineering Details and Professionalism

#### 4.1 Error handling, logging, validation, API design
- Conclusion: **Partial Pass**
- Rationale: standardized exception handlers and audit middleware exist, but validation gaps and inconsistent contract handling remain.
- Evidence: `repo/backend/app/core/exceptions.py:70`, `repo/backend/app/core/middleware.py:33`, `repo/backend/app/core/middleware.py:41`, `repo/backend/app/api/v1/endpoints/registrations.py:65`, `repo/backend/app/api/v1/endpoints/registrations.py:70`, `repo/backend/app/api/v1/endpoints/funding.py:424`, `repo/backend/app/api/v1/endpoints/funding.py:430`
- Manual verification note: runtime error-path UX still needs manual API exercise.

#### 4.2 Product/service maturity vs demo level
- Conclusion: **Partial Pass**
- Rationale: broad product modules and UIs are present, but several “critical-path” behaviors are inconsistent/incomplete for production acceptance.
- Evidence: `repo/frontend/src/views/ReviewDashboard.vue:112`, `repo/backend/app/api/v1/endpoints/backups.py:22`, `repo/backend/app/api/v1/endpoints/backups.py:137`, `repo/backend/app/core/token_blacklist.py:2`
- Manual verification note: requires runtime and operational hardening validation.

### 5. Prompt Understanding and Requirement Fit

#### 5.1 Business goal/constraint fit
- Conclusion: **Partial Pass**
- Rationale: major business domains were implemented, but key constraint semantics are violated (deadline/update rules, backup coverage, real-time validation expectations, role scoping).
- Evidence: `prompt.md:1`, `prompt.md:3`, `prompt.md:7`, `repo/backend/app/api/v1/endpoints/registrations.py:148`, `repo/backend/app/api/v1/endpoints/registrations.py:198`, `repo/backend/app/api/v1/endpoints/backups.py:69`, `repo/backend/app/api/v1/endpoints/materials.py:192`, `repo/frontend/src/views/RegistrationWizard.vue:53`, `repo/frontend/src/views/RegistrationWizard.vue:179`
- Manual verification note: browser-level UX of “real-time” validation requires manual confirmation.

### 6. Aesthetics (Frontend)

#### 6.1 Visual and interaction quality
- Conclusion: **Cannot Confirm Statistically**
- Rationale: static CSS/component structure indicates basic hierarchy, separation, and some interaction states, but visual quality and rendering correctness need browser verification.
- Evidence: `repo/frontend/src/App.vue:53`, `repo/frontend/src/views/ActivityList.vue:18`, `repo/frontend/src/views/FinancialDashboard.vue:340`, `repo/frontend/src/views/FinancialDashboard.vue:366`, `repo/frontend/src/components/GlobalToast.vue:73`
- Manual verification note: verify cross-browser/mobile rendering, spacing/alignment, and interactive states in a real browser.

## 5. Issues / Suggestions (Severity-Rated)

### Blocker

1. Severity: **Blocker**
Title: Missing required `ENCRYPTION_KEY` in run/config docs and compose
Conclusion: **Fail**
Evidence: `repo/backend/app/core/config.py:11`, `repo/backend/app/core/config.py:15`, `repo/README.md:45`, `repo/README.md:52`, `repo/docker-compose.yml:29`, `repo/docker-compose.yml:33`
Impact: documented startup path is statically invalid; app settings initialization can fail before serving API.
Minimum actionable fix: add `ENCRYPTION_KEY` to `.env` documentation, compose env, and provide a reproducible key-generation step (or `.env.example`).

2. Severity: **Blocker**
Title: No first-run bootstrap path for initial system administrator
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/auth.py:20`, `repo/backend/app/api/v1/endpoints/users.py:16`, `repo/README.md:64`, `repo/README.md:82`
Impact: clean deployment has no documented path to create the first admin, blocking user provisioning and core role-based flows.
Minimum actionable fix: add bootstrap mechanism (migration seed/init command) and document it in startup instructions.

### High

3. Severity: **High**
Title: Backup/restore targets wrong storage path for applicant materials
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/materials.py:192`, `repo/backend/app/api/v1/endpoints/backups.py:69`, `repo/backend/app/api/v1/endpoints/backups.py:73`, `repo/backend/app/api/v1/endpoints/backups.py:133`, `repo/docker-compose.yml:33`
Impact: backup claims “DB + materials” but excludes core material uploads; one-click recovery is incomplete.
Minimum actionable fix: backup/restore `settings.STORAGE_PATH` for materials (and include invoices/reports explicitly as separate scopes).

4. Severity: **High**
Title: Registration update endpoint permits non-draft mutations
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/registrations.py:148`, `repo/backend/app/api/v1/endpoints/registrations.py:198`, `docs/api-spec.md:675`, `docs/api-spec.md:698`
Impact: submitted/supplemented records can be altered by applicants, weakening review integrity and traceability.
Minimum actionable fix: enforce status guard (`draft` only, plus tightly scoped supplementary exception if required by policy).

5. Severity: **High**
Title: Registration creation lacks activity deadline enforcement
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/registrations.py:65`, `repo/backend/app/api/v1/endpoints/registrations.py:70`, `docs/api-spec.md:583`, `docs/api-spec.md:594`
Impact: applicants can create new registrations against expired activities.
Minimum actionable fix: reject creation when `activity.deadline < now` with `DEADLINE_PASSED`.

6. Severity: **High**
Title: API documentation materially diverges from implemented contracts
Conclusion: **Fail**
Evidence: `docs/api-spec.md:974`, `repo/backend/app/api/v1/endpoints/materials.py:407`, `docs/api-spec.md:2211`, `repo/backend/app/api/v1/endpoints/materials.py:37`, `docs/api-spec.md:238`, `docs/api-spec.md:267`, `repo/backend/app/api/v1/endpoints/users.py:40`, `repo/backend/app/api/v1/endpoints/users.py:49`, `repo/README.md:124`
Impact: static verification and client integration reliability are degraded; acceptance hard-gate 1.1 is not satisfied.
Minimum actionable fix: align docs and code (paths, methods, and response schema) and fix documentation links/locations.

7. Severity: **High**
Title: Financial admin registration listing scope exceeds documented least-privilege
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/registrations.py:108`, `repo/backend/app/api/v1/endpoints/registrations.py:111`, `docs/api-spec.md:600`
Impact: financial admins can read non-approved registrations, increasing unnecessary data exposure.
Minimum actionable fix: apply role-based scope filter so financial admins see approved/funding-relevant records only.

8. Severity: **High**
Title: Backup restore uses unsafe tar extraction
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/backups.py:132`, `repo/backend/app/api/v1/endpoints/backups.py:133`
Impact: crafted tar archives can write outside intended directories (path traversal risk).
Minimum actionable fix: validate tar members before extraction (reject absolute/parent traversal paths) and extract into controlled sandbox path.

### Medium

9. Severity: **Medium**
Title: Frontend logout does not invoke backend token revocation
Conclusion: **Partial Pass**
Evidence: `repo/frontend/src/App.vue:19`, `repo/frontend/src/stores/auth.store.js:59`, `repo/frontend/src/stores/auth.store.js:65`, `repo/backend/app/api/v1/endpoints/auth.py:129`, `repo/backend/app/api/v1/endpoints/auth.py:134`
Impact: JWT revocation mechanism is bypassed by normal UI logout flow.
Minimum actionable fix: call `POST /auth/logout` in `authStore.logout()` before clearing local state.

10. Severity: **Medium**
Title: Guest registration UI conflicts with admin-only backend registration policy
Conclusion: **Fail**
Evidence: `repo/frontend/src/router/index.js:21`, `repo/frontend/src/router/index.js:24`, `repo/frontend/src/stores/auth.store.js:46`, `repo/frontend/src/stores/auth.store.js:51`, `repo/backend/app/api/v1/endpoints/auth.py:20`
Impact: visible applicant signup path fails under normal guest usage and causes product-flow confusion.
Minimum actionable fix: either remove guest signup UI or implement a true public applicant onboarding flow consistent with policy.

11. Severity: **Medium**
Title: Wizard lacks client-side real-time file type/size checks
Conclusion: **Partial Pass**
Evidence: `repo/frontend/src/views/RegistrationWizard.vue:53`, `repo/frontend/src/views/RegistrationWizard.vue:179`, `prompt.md:1`
Impact: requirement of real-time validation is only partially met (server-side rejection after upload).
Minimum actionable fix: add immediate client checks (`accept`, extension/size guards, pre-upload feedback) aligned with backend limits.

12. Severity: **Medium**
Title: Data collection validation engine is only partially implemented
Conclusion: **Partial Pass**
Evidence: `repo/backend/app/api/v1/endpoints/data_collection.py:72`, `repo/backend/app/api/v1/endpoints/data_collection.py:76`, `repo/backend/app/api/v1/endpoints/data_collection.py:79`, `repo/backend/app/api/v1/endpoints/data_collection.py:104`, `prompt.md:5`
Impact: batch validation does not fully enforce stated type/range/mandatory rule coverage or full whitelist dimensions.
Minimum actionable fix: implement configurable rule pipeline (type/range/mandatory consistency) and honor whitelist dimensions beyond `activity_ids`.

13. Severity: **Medium**
Title: Invoice upload lacks documented file type/size validation
Conclusion: **Fail**
Evidence: `repo/backend/app/api/v1/endpoints/funding.py:424`, `repo/backend/app/api/v1/endpoints/funding.py:430`, `docs/api-spec.md:1701`, `docs/api-spec.md:1717`
Impact: unsupported or oversized invoice files can be stored, increasing security/storage risk.
Minimum actionable fix: enforce invoice extension and size validation before write.

14. Severity: **Medium**
Title: Material post-deadline lock check is incomplete for label updates
Conclusion: **Partial Pass**
Evidence: `repo/backend/app/api/v1/endpoints/materials.py:393`, `repo/backend/app/api/v1/endpoints/materials.py:401`, `repo/backend/app/models/registration.py:16`, `repo/backend/app/api/v1/endpoints/reviews.py:81`, `prompt.md:1`
Impact: lock logic depends on `registration.is_locked`, but no code path sets this true on deadline; label changes may bypass intended lock semantics.
Minimum actionable fix: enforce deadline-based lock checks consistently (not only `is_locked`) and implement explicit lock-state transition logic.

## 6. Security Review Summary
- Authentication entry points: **Partial Pass**. Login/hash/salt/lockout are implemented (`repo/backend/app/api/v1/endpoints/auth.py:46`, `repo/backend/app/api/v1/endpoints/auth.py:89`, `repo/backend/app/core/security.py:30`), but first-admin bootstrap is missing and blacklist persistence is in-memory only (`repo/backend/app/core/token_blacklist.py:2`).
- Route-level authorization: **Partial Pass**. Most endpoints use role checks/dependencies (`repo/backend/app/api/deps.py:68`, `repo/backend/app/api/deps.py:83`), but role scope is over-broad in some flows (e.g., financial admin listing all registrations: `repo/backend/app/api/v1/endpoints/registrations.py:108`).
- Object-level authorization: **Partial Pass**. Applicant ownership checks are present (`repo/backend/app/api/v1/endpoints/registrations.py:142`, `repo/backend/app/api/v1/endpoints/materials.py:136`, `repo/backend/app/api/v1/endpoints/funding.py:225`), but least-privilege exposure remains in cross-role listing scope.
- Function-level authorization: **Partial Pass**. Critical functions enforce role checks inline (e.g., reviews/funding transactions: `repo/backend/app/api/v1/endpoints/reviews.py:118`, `repo/backend/app/api/v1/endpoints/funding.py:105`).
- Tenant/user isolation: **Partial Pass**. Single-tenant design with user-level checks for applicant data exists; no explicit tenant boundary model is implemented (`repo/backend/app/models/registration.py:10`).
- Admin/internal/debug endpoint protection: **Pass**. Alerts/audit-logs/backups/data-collection admin endpoints depend on superuser checks (`repo/backend/app/api/v1/endpoints/alerts.py:21`, `repo/backend/app/api/v1/endpoints/audit_logs.py:22`, `repo/backend/app/api/v1/endpoints/backups.py:25`, `repo/backend/app/api/v1/endpoints/data_collection.py:26`).

## 7. Tests and Logging Review
- Unit tests: **Partial Pass**. Frontend unit coverage is minimal and focused on basic rendering/toast behavior (`repo/frontend/tests/App.spec.js:7`, `repo/frontend/tests/ActivityList.spec.js:13`, `repo/frontend/tests/GlobalToast.spec.js:15`).
- API / integration tests: **Partial Pass**. Backend has broad API-focused tests for many flows (`repo/backend/tests/test_business.py:68`, `repo/backend/tests/test_auth.py:46`, `repo/backend/tests/test_audit_coverage.py:192`), but key high-risk gaps remain (deadline creation/update constraints, backup correctness, invoice validation, scope overexposure).
- Logging categories / observability: **Partial Pass**. Audit middleware and module loggers exist (`repo/backend/app/core/middleware.py:12`, `repo/backend/app/api/v1/endpoints/reports.py:21`, `repo/backend/app/api/v1/endpoints/backups.py:78`), but logging is sparse and largely success-path oriented (`repo/backend/app/core/middleware.py:41`).
- Sensitive-data leakage risk in logs / responses: **Partial Pass**. Sensitive verification endpoint is role-gated (`repo/backend/app/api/v1/endpoints/reviews.py:286`), but restore failure returns raw exception text to clients (`repo/backend/app/api/v1/endpoints/backups.py:137`).

## 8. Test Coverage Assessment (Static Audit)

### 8.1 Test Overview
- Unit/API test presence: backend pytest suite exists across auth/activities/business/integration/hardening/audit files (`repo/backend/tests/test_auth.py:5`, `repo/backend/tests/test_business.py:68`, `repo/backend/tests/test_phase6_hardening.py:39`). Frontend vitest suite exists but limited (`repo/frontend/tests/App.spec.js:1`).
- Frameworks: pytest/vitest declared (`repo/backend/requirements.txt:28`, `repo/frontend/package.json:10`, `repo/frontend/package.json:24`).
- Test entry points: backend via pytest, frontend via `npm run test:unit` (`repo/README.md:103`, `repo/README.md:118`).
- Documentation for test commands: present (`repo/README.md:101`, `repo/README.md:119`).

### 8.2 Coverage Mapping Table

| Requirement / Risk Point | Mapped Test Case(s) | Key Assertion / Fixture / Mock | Coverage Assessment | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| Auth login + lockout (10 fails/5 min/30 min) | `repo/backend/tests/test_auth.py:46` | Asserts `is_locked` then 423 on next attempt (`repo/backend/tests/test_auth.py:67`, `repo/backend/tests/test_auth.py:75`) | basically covered | No persistence/restart behavior coverage for blacklist/lock state | Add restart/persistence tests for token revocation and lock state behavior |
| Unauthenticated 401 and role 403 (activities) | `repo/backend/tests/test_activities.py:153`, `repo/backend/tests/test_activities.py:182` | 401/403 assertions on create/update/delete | sufficient | Coverage concentrated on activities; not all critical modules | Add route-auth matrix tests for backups/reports/data-collection/material downloads |
| Applicant object-level isolation | `repo/backend/tests/test_phase6_hardening.py:39` | Applicant cannot GET/PATCH another applicant registration (`repo/backend/tests/test_phase6_hardening.py:69`, `repo/backend/tests/test_phase6_hardening.py:78`) | basically covered | No negative tests for financial-admin over-broad registration scope | Add tests asserting financial admins are restricted to approved/funding-relevant records |
| Review state transitions + supplementary one-time | `repo/backend/tests/test_business.py:195`, `repo/backend/tests/test_audit_remediation.py:24` | Requires correction reason; second correction blocked (`repo/backend/tests/test_audit_remediation.py:63`) | sufficient | No batch-size boundary test at 51 items | Add explicit 51-item batch rejection test |
| Overspend confirmation create/update | `repo/backend/tests/test_business.py:369`, `repo/backend/tests/test_audit_remediation.py:65` | 403 warning then success with `override_confirmed=true` (`repo/backend/tests/test_audit_remediation.py:95`, `repo/backend/tests/test_audit_remediation.py:105`) | sufficient | No test for exact threshold boundary behavior | Add tests for exactly 110% and 110%+epsilon |
| Duplicate SHA-256 submission rejection | `repo/backend/tests/test_business.py:449` | Second identical upload returns 400 duplicate (`repo/backend/tests/test_business.py:479`) | basically covered | No concurrency/race coverage | Add concurrent upload test to detect duplicate race conditions |
| Create registration must enforce activity deadline | No direct test | N/A | missing | Feature and tests both missing | Add test creating registration on expired activity expecting `DEADLINE_PASSED` |
| Update registration should be draft-only | No direct test | N/A | missing | High-risk state-integrity gap untested | Add tests to reject update for `submitted/supplemented` statuses |
| Backup includes materials and safe restore | Only access-control test: `repo/backend/tests/test_phase6_hardening.py:123` | Asserts role access only (`repo/backend/tests/test_phase6_hardening.py:131`) | insufficient | No correctness/safety tests for data scope/path traversal | Add tests verifying STORAGE_PATH backup/restore + malicious tar path rejection |
| Data collection rule coverage (type/range/mandatory + whitelist dimensions) | No meaningful rule-depth tests | N/A | missing | Batch engine partially implemented and unverified | Add tests for type/range/mandatory checks and whitelist filters (`status`, rule types) |
| Frontend core business flows (wizard/review/finance/admin) | No meaningful tests for these pages | Existing tests are basic render/toast only (`repo/frontend/tests/ActivityList.spec.js:13`) | insufficient | Severe UI-flow coverage gaps | Add vitest component tests for RegistrationWizard, ReviewDashboard, FinancialDashboard, SystemAdmin flows |

### 8.3 Security Coverage Audit
- Authentication: **Basically covered**, via login success/failure/lockout/logout token revoke tests (`repo/backend/tests/test_auth.py:5`, `repo/backend/tests/test_audit_remediation_high.py:175`).
- Route authorization: **Partially covered**, strong on activities/backups; weak on full admin/internal endpoint matrix.
- Object-level authorization: **Partially covered**, applicant isolation tested; financial-admin data-scope restrictions not tested.
- Tenant/data isolation: **Partially covered**, user-level isolation tested in single-tenant context; no tenant model tests (N/A for explicit tenancy model).
- Admin/internal protection: **Partially covered**, backup/metrics/admin access has tests (`repo/backend/tests/test_phase6_hardening.py:123`, `repo/backend/tests/test_phase5_integration.py:110`), but reports/audit-logs/data-collection coverage remains thin.

### 8.4 Final Coverage Judgment
**Fail**

Major risks covered: authentication lockout basics, core review and transaction overspend confirmation, duplicate upload detection, and key activity auth checks.

Major uncovered risks: deadline and state-integrity controls, backup data correctness/security, financial-admin least-privilege scope, data-collection rule depth, and frontend critical business workflows. Current tests could pass while severe defects remain in production-critical paths.

## 9. Final Notes
- This assessment is strictly static; no runtime claims are made.
- The strongest blockers are startup/config bootstrap viability and backup correctness against prompt-critical data integrity requirements.
- The codebase is close in feature breadth but not acceptance-ready under the provided hard gates.
