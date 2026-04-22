# Delivery Acceptance and Project Architecture Audit (Static-Only)

Date: 2026-04-22  
Scope root: `./repo`  
Audit mode: Static-only (no runtime execution)

## 1. Verdict
- **Overall conclusion: Fail**
- Rationale: multiple **Blocker/High** defects in migration bootstrap, auditing reliability, and recovery path reliability prevent acceptance as a verifiable, production-grade delivery.

## 2. Scope and Static Verification Boundary
- **Reviewed**:
  - Documentation and setup/test instructions: `repo/README.md`, `repo/.env.example`, `repo/run_tests.sh`, `repo/docker-compose.yml`
  - Backend entry points/routes/deps/services/models/migrations/tests
  - Frontend router/views/services/stores/tests
- **Not reviewed**:
  - Runtime behavior under actual server/browser/DB execution
  - Docker/container orchestration behavior
  - Performance under load/concurrency
- **Intentionally not executed**:
  - Project startup
  - Docker
  - Tests (`pytest`, `vitest`)
- **Manual verification required for**:
  - Real runtime behavior of backup restore on PostgreSQL
  - Browser rendering/interaction details
  - End-to-end flows requiring running frontend + backend

## 3. Repository / Requirement Mapping Summary
- **Prompt core goal mapped**: closed-loop registration-review-funding-audit platform for applicant/reviewer/financial admin/system admin.
- **Core flows mapped**:
  - Auth and role guards (`repo/backend/app/api/deps.py:32-96`, routes under `repo/backend/app/api/v1/routes/`)
  - Registration/checklist/material/version/review/funding (`repo/backend/app/services/phase4_*.py`)
  - Metrics/alerts/reports/data collection/backups (`repo/backend/app/services/phase5_*.py`, `backup_service.py`)
  - Frontend role portals (`repo/frontend/src/views/*.vue`, router guards)
- **Major constraints mapped**:
  - File limits and SHA-256 duplicate checks (`repo/backend/app/services/phase4_materials.py:71-90`)
  - Batch review max 50 (`repo/backend/app/services/phase4_review.py:128-130`)
  - 72h supplementary window (`repo/backend/app/services/phase4_review.py:91-94`, `phase4_materials.py:65-69`)
  - Account lockout rule (`repo/backend/app/services/auth_service.py:31-49`)

## 4. Section-by-section Review

### 4.1 Hard Gates

#### 1.1 Documentation and static verifiability
- **Conclusion: Fail**
- **Rationale**:
  - Startup path is statically inconsistent because migration chain is broken.
  - Test path is statically inconsistent due fixture/config signature mismatches.
- **Evidence**:
  - `repo/backend/docker-entrypoint.sh:20` runs `alembic upgrade head`
  - `repo/backend/alembic/versions/20260427_000007_backup_records.py:14-16` defines revision `20260427_000007`
  - `repo/backend/alembic/versions/20260428_000008_revoked_tokens.py:13-15` references `down_revision = '000007'` (missing)
  - `repo/backend/tests/conftest.py:29,35` calls `clear_blocklist()` without args
  - `repo/backend/app/core/token_blocklist.py:9` requires `clear_blocklist(db: Session)`
  - `repo/backend/tests/conftest.py:7` sets `SYSTEM_ADMIN_PASSWORD=AdminP@ss1`
  - `repo/backend/app/core/config.py:35-36` rejects `AdminP@ss1`
- **Manual verification note**: Not needed for the above inconsistencies; they are statically evident.

#### 1.2 Material deviation from Prompt
- **Conclusion: Partial Pass**
- **Rationale**:
  - Most domain modules and flows align with Prompt.
  - Material gaps remain (auditing reliability defect, incomplete export UX coverage, whitelist export path not explicit).
- **Evidence**:
  - Core domain coverage exists: `repo/backend/app/services/phase4_registration.py`, `phase4_materials.py`, `phase4_review.py`, `phase4_funding.py`, `phase5_reports_service.py`
  - Export UX currently centered on audit CSV only: `repo/frontend/src/views/SystemAdminConsole.vue:132-152,291-296`
  - No explicit whitelist export endpoint in phase-5 routes: `repo/backend/app/api/v1/routes/phase5_routes.py:198-254`
- **Manual verification note**: Runtime UX completeness should be manually checked.

### 4.2 Delivery Completeness

#### 2.1 Coverage of explicitly stated core requirements
- **Conclusion: Partial Pass**
- **Rationale**:
  - Many core requirements are implemented (auth, workflow, materials, funding, metrics, backups, similarity reserved).
  - High-impact gaps/defects affect acceptance of critical requirements (access auditing reliability, PostgreSQL recovery reliability, export completeness).
- **Evidence**:
  - Similarity reserved/disabled: `repo/backend/app/api/v1/routes/phase5_routes.py:366-379`
  - File validation/versioning/duplicate checks: `repo/backend/app/services/phase4_materials.py:73-89,97-113,120-149`
  - Access auditing defect path: `repo/backend/app/services/audit_log_service.py:107`, `repo/backend/app/core/token_blocklist.py:23-25`, `repo/backend/app/middleware/audit_middleware.py:41-44`

#### 2.2 End-to-end deliverable vs partial demo
- **Conclusion: Partial Pass**
- **Rationale**:
  - Repository structure is complete full-stack, not a toy snippet.
  - Static blockers prevent straightforward verification of documented bootstrap path.
- **Evidence**:
  - Full structure and docs: `repo/README.md:50-119`
  - Bootstrap blocker in migrations: `repo/backend/alembic/versions/20260428_000008_revoked_tokens.py:13-15`
- **Manual verification note**: End-to-end runtime verification remains required after fixing blockers.

### 4.3 Engineering and Architecture Quality

#### 3.1 Engineering structure and module decomposition
- **Conclusion: Pass**
- **Rationale**:
  - Backend is modularized by domain/service/repository/api layers; frontend has router/views/services/stores separation.
- **Evidence**:
  - Backend layout documented: `repo/README.md:101-106`
  - Layered backend package structure: `repo/backend/app/`
  - Router aggregation: `repo/backend/app/api/v1/router.py:3-26`
  - Frontend modular routes/views/services: `repo/frontend/src/router/index.js:15-80`, `repo/frontend/src/services/*.js`

#### 3.2 Maintainability and extensibility
- **Conclusion: Partial Pass**
- **Rationale**:
  - General extensible structure exists.
  - Several cross-module inconsistencies (migration IDs, API contract mismatch in stats key, auditing helper mismatch) reduce maintainability.
- **Evidence**:
  - Migration chain inconsistency: `repo/backend/alembic/versions/20260427_000007_backup_records.py:14-16`, `20260428_000008_revoked_tokens.py:13-15`
  - Stats contract mismatch: backend `period` key (`repo/backend/app/services/phase5_funding_statistics.py:123-141`) vs frontend `time_bucket` (`repo/frontend/src/views/FinancialDashboard.vue:229-231`)
  - Token blocklist helper mismatch in audit service: `repo/backend/app/services/audit_log_service.py:107`

### 4.4 Engineering Details and Professionalism

#### 4.1 Error handling, logging, validation, API design
- **Conclusion: Fail**
- **Rationale**:
  - Error envelope handling and validation patterns exist.
  - Critical logging/recovery defects materially affect professionalism and operability.
- **Evidence**:
  - Global error handlers: `repo/backend/app/main.py:67-112`
  - Validation examples: `repo/backend/app/schemas/registration_domain.py:39-55,119-160`
  - Audit logging failure path: `repo/backend/app/services/audit_log_service.py:107`, `repo/backend/app/middleware/audit_middleware.py:41-44`
  - Recovery path concerns (PostgreSQL): `repo/backend/app/services/backup_service.py:41-65,166-167,285-287`

#### 4.2 Product-like deliverable vs demo
- **Conclusion: Partial Pass**
- **Rationale**:
  - Delivery looks like a productized full-stack app with multiple role UIs and backend domains.
  - Some critical operational/security requirements are not reliably met due defects above.
- **Evidence**:
  - Multi-role frontend routes: `repo/frontend/src/router/index.js:25-79`
  - Domain breadth in backend services: `repo/backend/app/services/phase4_*.py`, `phase5_*.py`, `backup_service.py`

### 4.5 Prompt Understanding and Requirement Fit

#### 5.1 Business goal, semantics, constraints fit
- **Conclusion: Partial Pass**
- **Rationale**:
  - Business semantics are largely understood and implemented.
  - Requirement-level misses remain in reliability/completeness (access auditing reliability, export/whitelist completeness, alert triggering strategy).
- **Evidence**:
  - Workflow and supplementary logic: `repo/backend/app/services/phase4_review.py:32-47,91-105`, `phase4_materials.py:65-69,136-140`
  - Batch limit: `repo/backend/app/services/phase4_review.py:128-130`
  - Alert triggering limited by call path: `repo/backend/app/services/phase5_quality_metrics.py:109-112`, `repo/backend/app/api/v1/routes/phase5_routes.py:35-44`

### 4.6 Aesthetics (frontend)

#### 6.1 Visual/interaction quality fit
- **Conclusion: Cannot Confirm Statistically**
- **Rationale**:
  - Static code shows structured layouts, hover/disabled states, modal feedback, and responsive media query usage.
  - Rendering fidelity, visual consistency in-browser, and mobile behavior require runtime manual review.
- **Evidence**:
  - Interaction states/buttons/modals: `repo/frontend/src/views/ReviewDashboard.vue:228-295`, `FinancialDashboard.vue:288-301`
  - Responsive rules: `repo/frontend/src/views/FinancialDashboard.vue:448-455`
  - Global styling present but includes legacy/template-heavy rules: `repo/frontend/src/style.css:120-275`
- **Manual verification note**: Browser-based validation required for final UI acceptance.

## 5. Issues / Suggestions (Severity-Rated)

### Blocker

1) **Migration graph inconsistency blocks documented bootstrap path**
- **Severity**: Blocker
- **Conclusion**: Fail
- **Evidence**:
  - `repo/backend/alembic/versions/20260427_000007_backup_records.py:14-16`
  - `repo/backend/alembic/versions/20260428_000008_revoked_tokens.py:13-15`
  - `repo/backend/docker-entrypoint.sh:20`
- **Impact**:
  - `alembic upgrade head` is statically inconsistent; startup verification path is blocked.
- **Minimum actionable fix**:
  - Normalize `revision/down_revision` IDs in `20260428_000008_revoked_tokens.py` to point to actual predecessor (`20260427_000007`), regenerate/verify migration chain.

2) **Audit logging for authenticated mutating requests is broken**
- **Severity**: Blocker
- **Conclusion**: Fail
- **Evidence**:
  - `repo/backend/app/services/audit_log_service.py:107` (`is_jti_revoked(str(jti))`)
  - `repo/backend/app/core/token_blocklist.py:23-25` (`is_jti_revoked(db, jti)` signature)
  - `repo/backend/app/middleware/audit_middleware.py:41-44` (exceptions swallowed; log write rolled back)
- **Impact**:
  - Access auditing/traceability requirement is not reliably met; mutating operations may not be persisted to `audit_logs`.
- **Minimum actionable fix**:
  - Pass DB session to `is_jti_revoked`, add regression test for middleware-driven audit writes on authenticated POST/PUT/PATCH/DELETE.

### High

3) **PostgreSQL one-click restore path is likely non-functional on non-empty DBs**
- **Severity**: High
- **Conclusion**: Fail (Manual Verification Required)
- **Evidence**:
  - `repo/backend/app/services/backup_service.py:41-43` (`pg_dump` without `--clean`)
  - `repo/backend/app/services/backup_service.py:55-57` (`psql ... ON_ERROR_STOP=1`)
  - `repo/backend/app/services/backup_service.py:285-287` (restore executes SQL directly, no pre-clean/drop)
- **Impact**:
  - One-click recovery can fail in production PostgreSQL scenarios, undermining a core security/operations requirement.
- **Minimum actionable fix**:
  - Use clean restore strategy (`pg_dump --clean --if-exists` or restore into sanitized target), and add dedicated PostgreSQL restore integration tests.

4) **Documented test workflow is statically inconsistent**
- **Severity**: High
- **Conclusion**: Fail
- **Evidence**:
  - `repo/backend/tests/conftest.py:7` sets insecure default `AdminP@ss1`
  - `repo/backend/app/core/config.py:35-36` rejects `AdminP@ss1`
  - `repo/backend/tests/conftest.py:29,35` calls `clear_blocklist()` without args
  - `repo/backend/app/core/token_blocklist.py:9-11` requires `db` arg
- **Impact**:
  - Backend tests are not statically verifiable as runnable in a clean environment without manual intervention.
- **Minimum actionable fix**:
  - Update test defaults to secure credentials and fix fixture calls to token blocklist helpers (or provide test-safe wrapper API).

5) **Permission isolation gap: report metadata listing not scoped for financial admins**
- **Severity**: High
- **Conclusion**: Fail
- **Evidence**:
  - Route allows financial admins: `repo/backend/app/api/v1/routes/phase5_routes.py:336-339`
  - Service has no user-based filtering: `repo/backend/app/services/phase5_reports_service.py:288-321`
  - Download path enforces ownership only at download: `repo/backend/app/services/phase5_reports_service.py:327-329`
- **Impact**:
  - Cross-user report metadata enumeration is possible for financial admins.
- **Minimum actionable fix**:
  - Pass current user into `list_reports` and filter by `created_by` for `financial_admin` role.

### Medium

6) **Quality alert triggering is not automatic for global metrics path**
- **Severity**: Medium
- **Conclusion**: Partial Fail
- **Evidence**:
  - Alerts evaluated only when `activity_id` is present: `repo/backend/app/services/phase5_quality_metrics.py:109-112`
  - Global metrics endpoint omits `activity_id`: `repo/backend/app/api/v1/routes/phase5_routes.py:35-44`
- **Impact**:
  - Threshold breaches may not produce local alerts unless activity-scoped metrics are explicitly queried.
- **Minimum actionable fix**:
  - Trigger metric evaluation on relevant domain events (review/funding updates) or via periodic scheduler.

7) **Funding statistics API/Frontend contract mismatch for time grouping key**
- **Severity**: Medium
- **Conclusion**: Fail
- **Evidence**:
  - Backend emits `period`: `repo/backend/app/services/phase5_funding_statistics.py:123-141`
  - Frontend renders `time_bucket`: `repo/frontend/src/views/FinancialDashboard.vue:229-231`
- **Impact**:
  - Time-grouped statistics labels can render empty/incorrectly.
- **Minimum actionable fix**:
  - Align key names on both sides (`period` or `time_bucket`) and add UI contract tests.

8) **Data collection execution can 500 and leave batch state inconsistent**
- **Severity**: Medium
- **Conclusion**: Fail
- **Evidence**:
  - Marks `in_progress` then commits early: `repo/backend/app/services/phase5_data_collection_service.py:66-67`
  - Converts `activity_ids` via raw `uuid.UUID` without validation/rollback strategy: `repo/backend/app/services/phase5_data_collection_service.py:69`
- **Impact**:
  - Malformed whitelist input can crash execution and leave batch stuck in `in_progress`.
- **Minimum actionable fix**:
  - Validate whitelist payload before state transition; add exception handling to set status=`failed` and persist `error_message`.

9) **Frontend admin export coverage is incomplete vs stated scope**
- **Severity**: Medium
- **Conclusion**: Partial Fail
- **Evidence**:
  - Admin UI exposes only audit CSV generation flow: `repo/frontend/src/views/SystemAdminConsole.vue:132-152,291-296`
  - No `postComplianceReport` client function in phase5 service: `repo/frontend/src/services/phase5.service.js:1-69`
- **Impact**:
  - User-facing export capability does not fully cover reconciliation/audit/compliance workflows.
- **Minimum actionable fix**:
  - Add compliance/reconciliation generation and download flows in admin UI and service layer.

### Low

10) **Credential guidance mismatch in UI vs backend secure defaults**
- **Severity**: Low
- **Conclusion**: Fail
- **Evidence**:
  - UI hint says Docker default `admin/AdminP@ss1`: `repo/frontend/src/views/Login.vue:58`
  - Compose default password is different: `repo/docker-compose.yml:30`
  - Config rejects `AdminP@ss1`: `repo/backend/app/core/config.py:35-36`
- **Impact**:
  - Operator confusion during onboarding/manual verification.
- **Minimum actionable fix**:
  - Align login helper text with actual `.env`/compose defaults.

## 6. Security Review Summary

- **Authentication entry points**: **Partial Pass**
  - Evidence: login/logout/me/change-password routes exist with JWT (`repo/backend/app/api/v1/routes/auth.py:27-74`, `repo/backend/app/api/deps.py:32-57`), lockout logic implemented (`repo/backend/app/services/auth_service.py:31-49`).
  - Concern: auditability defect impacts security observability (`repo/backend/app/services/audit_log_service.py:107`).

- **Route-level authorization**: **Pass**
  - Evidence: role guards consistently used in routes (`users.py:28-84`, `funding_routes.py:34-173`, `backups.py:21-47`, `phase5_routes.py:35-379`).

- **Object-level authorization**: **Partial Pass**
  - Evidence: registration/material/review access checks (`repo/backend/app/services/phase4_access.py:29-46`, `phase4_materials.py:165-193`, `phase4_review.py:207-243`).
  - Gap: report listing lacks per-owner scoping for financial admins (`repo/backend/app/services/phase5_reports_service.py:288-321`).

- **Function-level authorization**: **Partial Pass**
  - Evidence: service-level role guards exist (`phase4_funding.py:77-80,138-139`, `phase4_sensitive.py:23-24`).
  - Gap: cross-user report metadata visibility remains.

- **Tenant/user data isolation**: **Partial Pass**
  - Evidence: applicant-scoped registration filters (`repo/backend/app/services/phase4_access.py:34-41`) and tested applicant isolation (`repo/backend/tests/test_phase6_hardening.py:138-199`).
  - Gap: report metadata isolation issue above.

- **Admin/internal/debug endpoint protection**: **Pass**
  - Evidence: sensitive admin endpoints protected (`repo/backend/app/api/v1/routes/backups.py:21-47`, `phase5_routes.py:85-254`).

## 7. Tests and Logging Review

- **Unit tests**: **Partial Pass**
  - Evidence: backend service/model tests exist (`repo/backend/tests/test_health_service.py`, `test_models.py`, `test_config_encryption.py`), frontend unit tests exist (`repo/frontend/src/__tests__/*.spec.js`).
  - Gap: critical helper/signature mismatches in fixtures reduce confidence (`repo/backend/tests/conftest.py:29,35` vs `repo/backend/app/core/token_blocklist.py:9`).

- **API / integration tests**: **Partial Pass**
  - Evidence: broad API coverage exists across auth/users/activities/phase4/phase5/phase6 tests.
  - Gap: missing tests for migration chain integrity and middleware audit path with token-blocklist call.

- **Logging categories / observability**: **Fail**
  - Evidence: middleware intended to log mutating requests (`repo/backend/app/middleware/audit_middleware.py:13-45`) but user resolution path is broken (`repo/backend/app/services/audit_log_service.py:107`).

- **Sensitive-data leakage risk in logs / responses**: **Partial Pass**
  - Evidence: no raw request body logging in audit middleware (`audit_middleware.py:34-40`), standardized errors (`main.py:67-112`).
  - Risk: admin/report metadata visibility and explicit sensitive verification responses require strict RBAC monitoring (`phase4_sensitive.py:50-56`, `phase5_reports_service.py:288-321`).

## 8. Test Coverage Assessment (Static Audit)

### 8.1 Test Overview
- **Unit tests exist**: Yes (backend + frontend)
  - Backend: `repo/backend/tests/test_health_service.py`, `test_models.py`, `test_config_encryption.py`
  - Frontend: `repo/frontend/src/__tests__/materialFile.spec.js`, `toastStore.spec.js`, etc.
- **API/integration tests exist**: Yes
  - Backend API suites: `test_auth_phase3.py`, `test_activities_api.py`, `test_phase4_business.py`, `test_phase5_api.py`, `test_phase6_hardening.py`
- **Frameworks**:
  - Backend: `pytest` (`repo/backend/pytest.ini:1-8`)
  - Frontend: `vitest` (`repo/frontend/package.json:10-11,24`)
- **Test entry points**:
  - Backend test path: `repo/backend/pytest.ini:4`
  - Combined script: `repo/run_tests.sh:10-31`
- **Documentation test commands**:
  - `repo/README.md:79-99`

### 8.2 Coverage Mapping Table

| Requirement / Risk Point | Mapped Test Case(s) (`file:line`) | Key Assertion / Fixture / Mock (`file:line`) | Coverage Assessment | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| Auth happy path + lockout policy | `repo/backend/tests/test_auth_phase3.py:17-45` | 200 login + 423 after 10 fails | sufficient | None major | Keep + add token-reuse/logout idempotency case |
| Unauthenticated 401 on protected routes | `repo/backend/tests/test_activities_api.py:216-218` | GET `/activities` returns 401 | basically covered | Not systematically across all sensitive endpoints | Parametrized 401 matrix for admin/funding/report/backups |
| Role-based 403 authorization | `repo/backend/tests/test_users_api.py:92-127`, `test_phase5_api.py:124-155` | applicant denied `/users`; applicant denied `/metrics/quality` | basically covered | Partial route surface only | Add route authorization matrix across phase4/phase5/backups |
| Object-level registration isolation | `repo/backend/tests/test_phase6_hardening.py:138-199` | Applicant A denied access to Applicant B registration | sufficient | Limited to registration object only | Add object-level tests for materials, invoices, audit/report objects |
| Batch review max 50 | `repo/backend/tests/test_phase6_hardening.py:120-135` | `BATCH_SIZE_EXCEEDED` on 54 IDs | sufficient | None major | Keep |
| Supplementary 72h + one-time correction rule | `repo/backend/tests/test_phase4_business.py:337-399`, `test_phase6_hardening.py:385-448` | `SUPPLEMENTARY_EXPIRED` and `SUPPLEMENTARY_EXHAUSTED` | sufficient | Edge cases around non-upload supplementary edits | Add test for label-only correction path semantics |
| Overspend confirmation flow | `repo/backend/tests/test_phase4_business.py:255-334,440-511` | 403 `OVERSPEND_CONFIRMATION_REQUIRED` then success with override | sufficient | Missing frontend contract assertion | Add frontend integration-like test for modal + confirm payload |
| Similarity interface reserved/disabled | `repo/backend/tests/test_phase5_api.py:28-37` | 501 `NOT_IMPLEMENTED` | sufficient | None major | Keep |
| Backup create/restore path | `repo/backend/tests/test_phase6_hardening.py:283-304` | create backup + sqlite restore success | basically covered | PostgreSQL restore not covered | Add PostgreSQL restore integration test with pre-existing schema/data |
| Audit logging reliability | `repo/backend/tests/test_phase5_api.py:55-59`, `test_phase6_hardening.py:631-638` | presence of login/failed-login logs | insufficient | Does not cover middleware mutating-request log path; misses current defect | Add test asserting audit row persisted for authenticated POST/PUT/PATCH/DELETE |
| Report access isolation | `repo/backend/tests/test_phase5_api.py:158-210` | owner-only download for financial admin | basically covered | List endpoint isolation not tested | Add `/reports` list ownership isolation test for financial admins |
| Frontend file validation | `repo/frontend/src/__tests__/materialFile.spec.js:9-32` | 20MB/200MB client validation | basically covered | Backend-side size/type edge tests sparse | Add backend API tests for boundary sizes and disallowed extensions |

### 8.3 Security Coverage Audit
- **Authentication**: **Basically covered** (login, lockout, password change) by `test_auth_phase3.py`, but fixture inconsistencies reduce trust in execution readiness.
- **Route authorization**: **Basically covered** with selected 403 checks (`test_users_api.py`, `test_phase5_api.py`), but not exhaustive.
- **Object-level authorization**: **Insufficient**; strong coverage for registration isolation, limited for other objects (reports list, invoices/material downloads).
- **Tenant/data isolation**: **Insufficient**; no tenant model and only partial per-user object checks.
- **Admin/internal protection**: **Basically covered** for backups and metrics endpoints (`test_phase6_hardening.py:283-293`, `test_phase5_api.py:124-155`).
- **Residual severe-defect risk**:
  - Middleware audit failure can remain undetected by current suite.
  - Migration chain integrity is untested.
  - PostgreSQL restore reliability is untested.

### 8.4 Final Coverage Judgment
- **Fail**
- Boundary explanation:
  - Covered: core auth, selected RBAC checks, key workflow and overspend path, basic backup flow (sqlite), similarity-disabled contract.
  - Uncovered/high-risk: migration integrity, middleware audit path, PostgreSQL restore correctness, report-list isolation, several cross-role/object-level boundaries.
  - Therefore tests could pass while severe production defects still remain.

## 9. Final Notes
- This audit is strictly static and evidence-based.
- The highest-priority acceptance blockers are migration chain consistency and audit logging reliability.
- After fixing blocker/high items, re-run a static check and then perform controlled manual/runtime verification for bootstrap, backups (PostgreSQL), and end-to-end role workflows.
