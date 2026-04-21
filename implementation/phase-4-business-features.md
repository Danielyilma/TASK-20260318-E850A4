## Phase 4: Business Features

### Goals
- Implement the core business features: Registrations, Material Uploads, Reviews, and Funding Accounts.
- Enable end-to-end processing of applications from submission to final financial tracking.

### Backend Implementation
1. **Database Models & Migrations:** Implement `Registration`, `MaterialChecklist`, `MaterialVersion`, `ReviewRecord`, `FundingAccount`, and `TransactionRecord`. Run `alembic revision --autogenerate`.
2. **Registration Endpoints:** Implement CRUD for `/registrations` according to `docs/api-spec.md`. Ensure strict validation of `form_data` and ensure `deadline` logic is respected. Implement `PATCH /submit` rules.
3. **Material Processing:**
   - Establish local file I/O operations (saving files securely).
   - Implement `POST /upload`. Compute `SHA-256` hash and run global duplicate checks. Check file sizes (single ≤20MB, total ≤200MB) and valid extensions.
   - Implement FIFO logic: when uploading a 4th material version, delete Version 1 from disk and database.
   - Endpoint: `/download` for retrieving files securely.
4. **Review State Machine:**
   - Implement `PATCH .../review`. Verify role, validate transitions (`submitted` -> `needs_correction`, `approved`, etc.), and handle the setting of `supplementary_requested_at` to trigger the 72h window.
   - Implement `POST /reviews/batch` supporting up to 50 items.
5. **Funding & Transactions:**
   - `FundingAccount` auto-creation on `approved` transition.
   - `POST .../transactions` logic. Check if expenses exceed 110% of `approved_budget`. If so, throw 403 `OVERSPEND_CONFIRMATION_REQUIRED`. If `override_confirmed` is true on subsequent request, commit transaction.

### Frontend Implementation
1. **Applicant Flows - Registration Wizard:**
   - Build a multi-step Vue.js form component to accommodate the initial form and the material checklist.
   - Provide file upload UI with real-time feedback on size validation and allowed types.
   - Implement the supplementary 72h countdown clock visually using backend timestamps.
2. **Reviewer Flows - Dashboard:**
   - Create a Review Dashboard displaying application lists with state filters.
   - Enable batch select checkboxes.
   - Build a modal for review actions (Approve, Reject, Needs Correction with reason text).
3. **Financial Admin Flows:**
   - Add a Financial Dashboard listing approved funding accounts.
   - Build transaction recording forms with invoice attachment support.
   - Handle the custom popup logic explicitly intercepting the overspending 110% warning from the API.

### Testing Plan
- **Endpoints:** Full coverage of all business logic endpoints using robust Pytest fixtures (setup activities, dummy users).
- **File System:** Mock file handling in tests or utilize a temporary testing directory. Write a test asserting that SHA-256 duplicate uploads fail (`test_duplicate_hash_rejection`).
- **State Machine Integration Tests:** Ensure transitions like `draft` -> `approved` fail directly without passing `submitted`. Ensure 72-hour `SUPPLEMENTARY_EXPIRED` logic behaves correctly during mocked timeline updates.
- **Frontend File Size Testing:** Use vitest to mock a 22MB file object and assert the frontend drops it before the API call.

### Definition of Done
- Full Applicant registration submission with file upload works top-to-bottom.
- Reviewer can approve an application, verifying transition logic.
- Financial Admin can record a transaction resulting in an overspend warning and subsequently confirm it.
