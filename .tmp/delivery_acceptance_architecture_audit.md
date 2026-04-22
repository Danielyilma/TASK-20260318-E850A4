# Delivery Acceptance and Project Architecture Audit (Static-Only)

Date: 2026-04-22  
Scope root: `repo/` (no runtime execution)

## 1. Verdict
- Overall conclusion: **Fail**
- Rationale: core prompt requirements have material gaps or high-risk defects in core flows (supplementary correction flow, PostgreSQL-targeted funding time statistics, report export path, backup/security requirements), despite substantial implemented surface area.

## 2. Scope and Static Verification Boundary
- Reviewed:
  - Documentation/config/manifests: `repo/README.md`, `repo/.env.example`, `repo/docker-compose.yml`, `docs/api-spec.md`, `docs/design.md`
  - Backend entrypoints/routes/deps/services/models/migrations
  - Frontend routes/views/services/stores
  - Backend and frontend test suites/config
- Not reviewed:
  - Runtime behavior in browser/container/networked deployment
  - External environment tools (`pg_dump`, `psql`) behavior in target host
- Intentionally not executed:
  - Project startup, Docker, tests, migrations, API calls
- Manual verification required:
  - PostgreSQL restore reliability and recovery semantics (`repo/backend/app/services/backup_service.py:40-63`, `:262-267`)
  - PostgreSQL execution of funding time grouping query (`repo/backend/app/services/phase5_funding_statistics.py:102-117`)
  - UI runtime rendering and interaction polish in real browser (static-only here)

## 3. Repository / Requirement Mapping Summary
- Prompt core goal mapped: applicant registration/material lifecycle, reviewer workflow/state machine, finance transactions/overspend handling, admin quality/audit/reports/backups, offline-local storage.
- Main implementation areas mapped:
  - Backend modules: auth/users/activities/registrations/materials/review/funding/phase5 metrics-alerts-reports/backups (`repo/backend/app/api/v1/router.py:17-26`)
  - Data model: registrations/checklists/versions/reviews/funding/accounts/transactions/batches/quality/alerts/reports/backups (`repo/backend/app/models/*.py`)
  - Frontend role-based pages and API clients (`repo/frontend/src/router/index.js:17-79`, `repo/frontend/src/views/*.vue`)
- Result: broad coverage exists, but multiple core requirement mismatches remain.

## 4. Section-by-section Review

### 4.1 Hard Gates
#### 4.1.1 Documentation and static verifiability
- Conclusion: **Partial Pass**
- Rationale: startup/test/config instructions exist and are mostly statically coherent, but delivered feature scope is not accurately documented in key docs.
- Evidence:
  - Startup/test/config guidance exists: `repo/README.md:27-98`, `repo/.env.example:1-19`, `repo/docker-compose.yml:1-53`
  - Backend entrypoint behavior aligns with docs: `repo/backend/docker-entrypoint.sh:20-24`
  - Scope drift in README (still phase-2 oriented while backend includes phase4/5/backups routers): `repo/README.md:5-7`, `repo/README.md:100-118`, `repo/backend/app/api/v1/router.py:21-26`
  - Frontend README is generic template, not delivery-specific: `repo/frontend/README.md:1-5`
- Manual verification note: none.

#### 4.1.2 Material deviation from prompt
- Conclusion: **Fail**
- Rationale: implementation includes relevant modules, but key prompt requirements are weakened or missing (supplementary process behavior, daily backups automation, sensitive config encryption, threshold-alert behavior).
- Evidence:
  - Supplementary flow locks too early after first upload: `repo/backend/app/services/phase4_materials.py:138-141`, `repo/backend/app/services/phase4_registration.py:42-50`
  - Daily auto backup not implemented (manual only): `repo/backend/app/services/backup_service.py:136-151`, `repo/backend/app/api/v1/routes/backups.py:33-39`
  - No sensitive config encryption mechanism in config/security path: `repo/backend/app/core/config.py:13-19`, `repo/backend/app/core/security.py:13-53`
  - Alerts tied to overspend events only; no quality-threshold-trigger pipeline: `repo/backend/app/services/phase5_alerts_service.py:25-52`, `repo/backend/app/services/phase5_quality_metrics.py:95-106`
- Manual verification note: daily scheduler could exist externally, but no in-repo static evidence.

### 4.2 Delivery Completeness
#### 4.2.1 Core requirements coverage
- Conclusion: **Fail**
- Rationale: many core requirements are implemented, but critical prompt items are incomplete or defective.
- Evidence:
  - Implemented: file type/size/total constraints and SHA-256 duplicate check: `repo/backend/app/services/phase4_materials.py:75-91`
  - Implemented: batch review size cap: `repo/backend/app/services/phase4_review.py:127-129`
  - Implemented: overspend secondary confirmation path: `repo/backend/app/services/phase4_funding.py:143-163`, `repo/frontend/src/views/FinancialDashboard.vue:250-261`
  - Missing/defective: supplementary correction process effectively single-upload: `repo/backend/app/services/phase4_materials.py:138-141`, `repo/backend/app/services/phase4_registration.py:42-50`
  - Missing: daily automatic backup evidence: `repo/backend/app/services/backup_service.py:136-151`
  - Missing: sensitive configuration encryption evidence: `repo/backend/app/core/config.py:13-19`
- Manual verification note: none.

#### 4.2.2 End-to-end deliverable shape (0→1)
- Conclusion: **Partial Pass**
- Rationale: repository is a full multi-module project (backend/frontend/tests/migrations), not a snippet/demo; however several critical business/security requirements are still not production-complete.
- Evidence:
  - Full structure: `repo/backend/app/*`, `repo/frontend/src/*`, `repo/backend/tests/*`, `repo/backend/alembic/versions/*`
  - Basic docs and run/test commands: `repo/README.md:27-98`
  - Known delivery-critical gaps listed in issues section.
- Manual verification note: none.

### 4.3 Engineering and Architecture Quality
#### 4.3.1 Structure and module decomposition
- Conclusion: **Pass**
- Rationale: backend is separated into routes/services/models/repositories/schemas; frontend split by views/services/stores.
- Evidence:
  - Backend modularity: `repo/backend/app/api/v1/router.py:17-26`, `repo/backend/app/services/*.py`, `repo/backend/app/models/*.py`
  - Frontend modularity: `repo/frontend/src/router/index.js:15-80`, `repo/frontend/src/services/*.js`, `repo/frontend/src/stores/*.js`
- Manual verification note: none.

#### 4.3.2 Maintainability/extensibility
- Conclusion: **Partial Pass**
- Rationale: codebase has maintainable layering, but portability and policy gaps reduce extensibility reliability.
- Evidence:
  - DB portability problem (SQLite-specific function used in core statistics path): `repo/backend/app/services/phase5_funding_statistics.py:103-117`
  - Contract/authorization mismatch on report download semantics: `docs/api-spec.md:2346`, `repo/backend/app/api/v1/routes/phase5_routes.py:346-353`, `repo/backend/app/services/phase5_reports_service.py:322-329`
  - Documentation drift reduces maintainability: `repo/README.md:5-7`, `repo/README.md:100-118`
- Manual verification note: PostgreSQL runtime validation needed.

### 4.4 Engineering Details and Professionalism
#### 4.4.1 Error handling/logging/validation/API detail
- Conclusion: **Partial Pass**
- Rationale: standardized error envelope and many validations exist, but observability and some critical paths are incomplete.
- Evidence:
  - Standard error handlers: `repo/backend/app/main.py:29-74`
  - Input validations present in schemas/services: `repo/backend/app/schemas/registration_domain.py:21-43`, `repo/backend/app/services/phase4_materials.py:75-91`
  - Audit logging only for mutating methods (GET access not audited): `repo/backend/app/middleware/audit_middleware.py:21-24`
  - No standard application logging instrumentation (no `logging` usage found across backend app code)
- Manual verification note: evaluate operational observability in deployment.

#### 4.4.2 Product/service maturity vs demo
- Conclusion: **Partial Pass**
- Rationale: project shape is product-like, but notable runtime defects and missing non-functional requirements keep it below acceptance maturity.
- Evidence:
  - Production-like components: JWT auth, RBAC, migrations, backup/report modules (`repo/backend/app/*`)
  - Runtime defect in report PDF path (`letter` undefined): `repo/backend/app/services/phase5_reports_service.py:89`, `:192`, `:256`
- Manual verification note: none.

### 4.5 Prompt Understanding and Requirement Fit
#### 4.5.1 Business goal/scenario/constraint fit
- Conclusion: **Fail**
- Rationale: broad feature intent matches, but key business/security constraints are not correctly realized.
- Evidence:
  - Prompt-fit positives: state machine + batch review + waitlist promote path: `repo/backend/app/services/phase4_review.py:32-47`, `:124-200`, `:255-289`
  - Prompt-fit gap: supplementary process behavior too restrictive: `repo/backend/app/services/phase4_materials.py:138-141`, `repo/backend/app/services/phase4_registration.py:42-50`
  - Prompt-fit gap: daily backups requirement not implemented as daily automation: `repo/backend/app/services/backup_service.py:136-151`
  - Prompt-fit gap: sensitive configuration encryption missing: `repo/backend/app/core/config.py:13-19`
- Manual verification note: none.

### 4.6 Aesthetics (Frontend)
#### 4.6.1 Visual/interaction quality and consistency
- Conclusion: **Partial Pass**
- Rationale: pages are structured with clear sections and interaction states, but visual language is inconsistent due leftover template/global styles and mixed design conventions.
- Evidence:
  - Functional visual structure and interactive feedback in views: e.g. `repo/frontend/src/views/ReviewDashboard.vue:133-205`, `repo/frontend/src/views/FinancialDashboard.vue:176-263`
  - Inconsistent global style baseline from template with different token/theme assumptions: `repo/frontend/src/style.css:1-31`, `:120-296`
- Manual verification note: full browser rendering and responsive behavior require manual UI check.

## 5. Issues / Suggestions (Severity-Rated)

### Blocker
1. **Blocker — Supplementary correction flow effectively allows only one upload**
   - Conclusion: Fail
   - Evidence: `repo/backend/app/services/phase4_materials.py:138-141`, `repo/backend/app/services/phase4_registration.py:42-50`, `repo/backend/app/services/phase4_materials.py:63-71`
   - Impact: Applicant cannot complete multi-item corrections within the 72-hour supplementary window; core correction workflow breaks.
   - Minimum actionable fix: keep supplementary window writable for all needed corrected materials until `supplementary_deadline`; do not set `supplementary_used`/lock on first file upload. Mark supplementary consumption at explicit final resubmission event.

2. **Blocker — Funding time statistics use SQLite-only SQL function on PostgreSQL target**
   - Conclusion: Fail
   - Evidence: `repo/backend/app/services/phase5_funding_statistics.py:103-117` (`func.strftime`), PostgreSQL target in project config/docs `repo/.env.example:4`, `repo/docker-compose.yml:3-7`
   - Impact: category/time statistics endpoint can fail in intended offline PostgreSQL deployment.
   - Minimum actionable fix: use dialect-agnostic or PostgreSQL-compatible date bucketing (`date_trunc` for month/quarter) with tested cross-dialect fallback.

### High
3. **High — PDF report generation path has undefined symbol `letter`**
   - Conclusion: Fail
   - Evidence: `repo/backend/app/services/phase5_reports_service.py:89`, `:192`, `:256` (uses `letter` with no import in file header `:1-22`)
   - Impact: PDF report export path for reconciliation/audit/compliance is broken.
   - Minimum actionable fix: import `letter` from `reportlab.lib.pagesizes` and add tests for all report formats.

4. **High — Daily automatic backup requirement not implemented in-repo**
   - Conclusion: Fail
   - Evidence: manual backup only `repo/backend/app/services/backup_service.py:136-151`; routes expose manual trigger only `repo/backend/app/api/v1/routes/backups.py:33-39`; no scheduler in startup/compose `repo/backend/docker-entrypoint.sh:20-24`, `repo/docker-compose.yml:1-53`
   - Impact: explicit requirement “daily local backups” is unmet.
   - Minimum actionable fix: add scheduled backup job (in-process scheduler or host cron integration) producing `backup_type=daily_auto` records.

5. **High — Sensitive configuration encryption requirement missing**
   - Conclusion: Fail
   - Evidence: secrets are plain config/env fields `repo/backend/app/core/config.py:13-19`; no config encryption/decryption mechanism in core security path `repo/backend/app/core/security.py:13-53`
   - Impact: explicit security requirement for sensitive config encryption is not met.
   - Minimum actionable fix: implement encrypted-at-rest configuration handling (key-managed decryption at startup) for sensitive settings.

6. **High — PostgreSQL one-click restore has high risk of failure (suspected)**
   - Conclusion: Suspected Risk / Cannot Confirm Statistically
   - Evidence: `pg_dump` executed without `--clean` `repo/backend/app/services/backup_service.py:42`; restore replays SQL into existing DB via `psql -f` `:55`, called at `:263`
   - Impact: restore may fail on existing schema/data, undermining one-click recovery in target deployment.
   - Minimum actionable fix: restore into clean DB (`--clean --if-exists`, controlled transactional restore path, pre-restore safety checks) plus PostgreSQL restore integration tests.

7. **High — Report download authorization is broader than documented contract**
   - Conclusion: Fail
   - Evidence: documented owner-or-admin constraint `docs/api-spec.md:2346`; implementation allows any financial_admin/system_admin without owner check `repo/backend/app/api/v1/routes/phase5_routes.py:346-353`, `repo/backend/app/services/phase5_reports_service.py:322-329`
   - Impact: financial admins may access admin-generated audit/compliance exports they did not create.
   - Minimum actionable fix: enforce ownership or explicit role-based scope per report type in `download_path`/route guard.

8. **High — Quality-threshold alert triggering not implemented beyond overspend transactions**
   - Conclusion: Fail
   - Evidence: quality metrics compute-only return path `repo/backend/app/services/phase5_quality_metrics.py:95-106`; alert creation logic only overspend-specific `repo/backend/app/services/phase5_alerts_service.py:25-52` and called only from funding transaction mutations `repo/backend/app/services/phase4_funding.py:186-189`, `:271-274`
   - Impact: requirement to trigger local alerts when metrics thresholds exceeded is not met for approval/correction/overspending-rate metrics.
   - Minimum actionable fix: add configurable thresholds and alert emission pipeline for quality metrics computation/scheduled jobs.

### Medium
9. **Medium — Access auditing is partial (mutating-only and no failed-login audit)**
   - Conclusion: Partial Fail
   - Evidence: audit middleware filters to POST/PUT/PATCH/DELETE only `repo/backend/app/middleware/audit_middleware.py:21-24`; login audit inserted only on success `repo/backend/app/api/v1/routes/auth.py:29-40`
   - Impact: incomplete forensic trail for read access and authentication failures.
   - Minimum actionable fix: expand audit policy to selected GET-sensitive endpoints and failed auth events with safe redaction.

10. **Medium — Documentation scope drift reduces static verifiability**
    - Conclusion: Fail
    - Evidence: README still phase-2 framing `repo/README.md:5-7`, `:100-118`; backend includes many phase4/5/backups routes `repo/backend/app/api/v1/router.py:21-26`; frontend README still template `repo/frontend/README.md:1-5`
    - Impact: reviewers/operators can misjudge actual delivered surface and verification steps.
    - Minimum actionable fix: refresh root/frontend docs to match current modules/endpoints/role flows and verification checklist.

11. **Medium — Logout endpoint likely returns 403 (not 401) on missing bearer token**
    - Conclusion: Partial Fail
    - Evidence: `HTTPBearer()` default in route `repo/backend/app/api/v1/routes/auth.py:24`, used by logout `:44-49`; contract documents 401 for missing/invalid token `docs/api-spec.md:85-88`
    - Impact: API contract inconsistency and client error-handling mismatch.
    - Minimum actionable fix: use `HTTPBearer(auto_error=False)` + explicit 401 handling aligned with error envelope.

12. **Medium — Data model FK semantics contain `SET NULL` with non-nullable columns**
    - Conclusion: Partial Fail
    - Evidence: examples `repo/backend/app/models/transaction_record.py:29-33`, `repo/backend/app/models/data_collection_batch.py:20-24`, `repo/backend/app/models/generated_report.py:23-27`, `repo/backend/app/models/sensitive_verification_audit.py:22-26`
    - Impact: deletion semantics are contradictory and can cause integrity/maintenance surprises.
    - Minimum actionable fix: align nullability and `ondelete` strategy (either nullable + SET NULL or non-null + RESTRICT/CASCADE).

13. **Medium — Frontend route/UI exposes activity-creation entry to non-admin roles**
    - Conclusion: Partial Fail
    - Evidence: route lacks role guard `repo/frontend/src/router/index.js:26-30`; button always shown in activities view `repo/frontend/src/views/ActivityList.vue:56`
    - Impact: role confusion and avoidable authorization errors.
    - Minimum actionable fix: add `roles: ['system_admin']` guard and conditional UI rendering by role.

## 6. Security Review Summary
- **Authentication entry points**: **Partial Pass**  
  Evidence: login/logout/me/change-password exist `repo/backend/app/api/v1/routes/auth.py:27-74`; lockout logic implemented `repo/backend/app/services/auth_service.py:31-77`.  
  Note: logout missing-token behavior likely 403 vs expected 401 (`repo/backend/app/api/v1/routes/auth.py:24`, `:44-49`).

- **Route-level authorization**: **Partial Pass**  
  Evidence: dependency guards used across routes (`require_system_admin`, `require_reviewer`, etc.) `repo/backend/app/api/deps.py:60-96`; examples on users/backups/phase5 routes `repo/backend/app/api/v1/routes/users.py:28-84`, `repo/backend/app/api/v1/routes/backups.py:21-47`, `repo/backend/app/api/v1/routes/phase5_routes.py:31-367`.  
  Gap: report download scope too broad (`repo/backend/app/api/v1/routes/phase5_routes.py:346-353`).

- **Object-level authorization**: **Partial Pass**  
  Evidence: registration ownership and role scoping `repo/backend/app/services/phase4_access.py:11-46`; material download checks registration access `repo/backend/app/services/phase4_materials.py:174-188`.  
  Gap: report download lacks object ownership policy (`repo/backend/app/services/phase5_reports_service.py:322-329`).

- **Function-level authorization**: **Pass**  
  Evidence: service-level role checks in materials/review/funding/sensitive services (`repo/backend/app/services/phase4_materials.py:50-55`, `repo/backend/app/services/phase4_review.py:71-73`, `repo/backend/app/services/phase4_funding.py:73-76`, `repo/backend/app/services/phase4_sensitive.py:23-26`).

- **Tenant / user isolation**: **Partial Pass**  
  Evidence: applicants restricted to own registrations (`repo/backend/app/services/phase4_access.py:14-16`, `:44-46`).  
  Gap: no multi-tenant model; isolation is user/role-only (acceptable if single-tenant, but tenant requirement cannot be confirmed).

- **Admin / internal / debug endpoint protection**: **Pass**  
  Evidence: admin routes guarded (`repo/backend/app/api/v1/routes/users.py:39-84`, `repo/backend/app/api/v1/routes/phase5_routes.py:31-367`, `repo/backend/app/api/v1/routes/backups.py:21-47`); no exposed debug routes identified.

## 7. Tests and Logging Review
- **Unit tests**: **Partial Pass**  
  Evidence: utility/component tests exist (`repo/frontend/src/__tests__/materialFile.spec.js:1-33`, `repo/frontend/src/__tests__/toastStore.spec.js:1-20`, `repo/backend/tests/test_health_service.py:1-7`).

- **API / integration tests**: **Partial Pass**  
  Evidence: broad backend API tests for auth/activities/phase4/phase5/phase6 (`repo/backend/tests/test_auth_phase3.py`, `test_activities_api.py`, `test_phase4_business.py`, `test_phase5_api.py`, `test_phase6_hardening.py`).

- **Logging categories / observability**: **Partial Fail**  
  Evidence: audit-log DB entries for mutating HTTP calls (`repo/backend/app/middleware/audit_middleware.py:21-37`), but no conventional application logging instrumentation in backend app code.

- **Sensitive-data leakage risk in logs/responses**: **Partial Fail**  
  Evidence: logs store method/path/status and not bearer token payload (`repo/backend/app/services/audit_log_service.py:149-151`) which is positive; however responses expose server file paths for some privileged endpoints (`repo/backend/app/schemas/backup_domain.py:14`, `repo/backend/app/schemas/registration_domain.py:340`) and route/service return those models.

## 8. Test Coverage Assessment (Static Audit)

### 8.1 Test Overview
- Unit and API tests exist in both backend and frontend.
- Frameworks:
  - Backend: `pytest`, `httpx`, `pytest-asyncio`, `pytest-cov` (`repo/backend/requirements.txt:12-17`, `repo/backend/pytest.ini:1-8`)
  - Frontend: `vitest`, `@vue/test-utils` (`repo/frontend/package.json:10-25`, `repo/frontend/vite.config.js:14-18`)
- Entry points:
  - Backend: `pytest` (`repo/README.md:82-88`)
  - Frontend: `npm run test:unit` (`repo/README.md:94-98`)
  - Combined script: `repo/run_tests.sh:10-31`
- Docs provide test commands: yes (`repo/README.md:78-98`)

### 8.2 Coverage Mapping Table
| Requirement / Risk Point | Mapped Test Case(s) | Key Assertion / Fixture / Mock | Coverage Assessment | Gap | Minimum Test Addition |
|---|---|---|---|---|---|
| Login success + JWT issuance | `repo/backend/tests/test_auth_phase3.py:16-29` | `status_code==200`, token/user fields | basically covered | no token claim validation | assert exp/jti/sub structure |
| Lockout after repeated failures | `repo/backend/tests/test_auth_phase3.py:32-45` | 10 failed + next returns 423 | basically covered | boundary at exact 10th attempt not asserted | add exact-threshold behavior test |
| Admin-only user creation | `repo/backend/tests/test_users_api.py:16-34`, `:92-127` | admin 201; applicant 403 | sufficient | none critical | add reviewer/finance role negative tests |
| Activity CRUD + auth | `repo/backend/tests/test_activities_api.py:25-117`, `:216-259` | 201/200/404/409/401/403 checks | sufficient | pagination/filter edge cases limited | add sort/search boundary tests |
| Registration create/upload/submit happy path | `repo/backend/tests/test_phase4_business.py:118-168` | checklist+upload+label+submit | basically covered | wizard multi-step permutations not covered | add multiple checklist item submit requirements |
| SHA-256 duplicate rejection | `repo/backend/tests/test_phase4_business.py:170-223`, `repo/backend/tests/test_phase6_hardening.py:305-367` | second upload 400 `DUPLICATE_FILE` | sufficient | cross-user cross-activity + race timing not fully stressed | add concurrent transaction-level uniqueness test |
| Review invalid transition | `repo/backend/tests/test_phase4_business.py:225-252` | draft→approve returns 400 | basically covered | full state machine matrix missing | add parametric transition matrix tests |
| Batch review limit <=50 | `repo/backend/tests/test_phase6_hardening.py:117-133` | 54 ids -> `BATCH_SIZE_EXCEEDED` | sufficient | exactly 50 success case missing | add boundary 50 pass / 51 fail |
| Overspend confirmation workflow | `repo/backend/tests/test_phase4_business.py:255-334`, `:440-511` | 403 confirmation required then success with override | sufficient | UI confirm flow not tested | add frontend test for overspend modal confirm |
| Supplementary window expiry | `repo/backend/tests/test_phase4_business.py:336-399` | forced past deadline -> `SUPPLEMENTARY_EXPIRED` | basically covered | multi-file supplementary behavior not tested | add test for multiple corrections within window |
| Sensitive verify endpoint + audit write | `repo/backend/tests/test_phase4_business.py:401-437`, `repo/backend/tests/test_phase6_hardening.py:200-264` | reviewer gets unmasked data and audit row | basically covered | financial-admin masking policy not tested | add role-based masking tests |
| Backups admin access + restore smoke | `repo/backend/tests/test_phase6_hardening.py:281-302` | applicant 403, admin backup+restore success (sqlite) | insufficient | PostgreSQL restore path untested | add PostgreSQL integration backup/restore tests |
| Similarity endpoint reserved disabled | `repo/backend/tests/test_phase5_api.py:28-37` | 501 `NOT_IMPLEMENTED` | sufficient | none | n/a |
| Router guard auth/role redirects (frontend) | `repo/frontend/src/__tests__/routerGuards.spec.js:12-42` | unauth redirect + role redirect | basically covered | backend authorization integration not covered | add API-mocked 403 handling UX tests |
| Client-side material size/type checks | `repo/frontend/src/__tests__/materialFile.spec.js:8-33` | 20MB/200MB/type checks | sufficient | checksum duplicate precheck absent by design | n/a |

### 8.3 Security Coverage Audit (Tests)
- Authentication: **Basically covered**  
  Evidence: login, lockout, password change, inactive user cases (`repo/backend/tests/test_auth_phase3.py:16-215`).
- Route authorization: **Partially covered**  
  Evidence: several 403 checks exist (`repo/backend/tests/test_users_api.py:92-127`, `repo/backend/tests/test_activities_api.py:222-259`, `repo/backend/tests/test_phase5_api.py:124-154`), but many protected endpoints lack role-negative tests.
- Object-level authorization: **Partially covered**  
  Evidence: applicant cannot read other applicant registration (`repo/backend/tests/test_phase6_hardening.py:136-197`); gaps remain for report/object ownership and material download ownership permutations.
- Tenant / data isolation: **Insufficient**  
  Evidence: only user-level isolation sample exists; no tenant boundary model/tests.
- Admin / internal protection: **Basically covered**  
  Evidence: backups/metrics/users role restrictions tested (`repo/backend/tests/test_phase6_hardening.py:281-290`, `repo/backend/tests/test_users_api.py:92-127`, `repo/backend/tests/test_phase5_api.py:124-154`).

### 8.4 Final Coverage Judgment
**Partial Pass**

Major happy paths and several critical security checks are covered, but severe defects could still remain undetected because tests do not cover PostgreSQL-specific behavior, full state-machine boundary cases, report ownership authorization, supplementary multi-file correction semantics, and daily-backup automation behavior.

## 9. Final Notes
- This audit is static-only; no runtime claim is made beyond code-level evidence.
- Highest-priority remediation order:
  1. Fix supplementary correction semantics and PostgreSQL time-stat query portability.
  2. Fix PDF report export runtime defect and tighten report download authorization.
  3. Implement daily automated backups + robust PostgreSQL restore procedure.
  4. Add security/authorization and PostgreSQL integration tests for uncovered high-risk paths.
