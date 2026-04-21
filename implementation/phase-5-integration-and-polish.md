## Phase 5: Integration & Polish

### Goals
- Unify the application layers with centralized error handling, robust logging, and data tracking features across both backend and frontend.
- Implement reporting, audits, metrics, and quality validation processes.

### Backend Implementation
1. **Unified Error Handling:** [x] Add FastAPI Exception Handlers to map generic error classes (like `ResourceNotFound`, `ValidationError`) to the standardized explicit JSON error response format from `api-spec.md`.
2. **Auditing Middleware/Interceptors:** [x] Create `AuditLog` database models. Use middleware or dependency injections to intercept `POST/PUT/PATCH/DELETE` calls, logging the action, `resource_type`, `resource_id`, and User ID into the Audit table asynchronously to prevent request bloat.
3. **Data Collection & Validations:** [x]
   - Implement `DataCollectionBatch` models and its APIs. [x]
   - Implement the `/execute` batch logic that loops over records matching the scope whitelist and performs rule-based validations, storing output into `QualityValidationResult`. [x]
4. **Metrics & Alerts:** [x]
   - Create logic behind `GET /metrics/quality` computing aggregate statistics dynamically. [x]
   - Define local alerts for scenarios like thresholds being surpassed. Provide alert APIs (`GET /alerts`, `PATCH .../acknowledge`). [x]
5. **Reports/Exports:** Support `xlsx`/`pdf` generation endpoints utilizing standard python reporting libraries (like `pandas`, `openpyxl`, or `ReportLab`). [x]

### Frontend Implementation
1. **Global Error Feedback:** [x] Implement a global Axios interceptor. On intercepting a 400 or 500 range standard error JSON, pop up a toast/notification using a component library (e.g., Vuetify, ElementPlus, or a custom toast).
2. **Loading States Component:** [x] Add widespread visual indications of processing—spinners on buttons, skeleton loaders for data tables.
3. **Alerts & System Admin Panel:** [x]
   - Construct an Alerts Inbox for the System Admin to view and acknowledge threshold breaches. [x]
   - Build UI for creating and viewing Data Collection Batches. [x]
   - Create Report generation UI letting users pick a timeline, type, and download the resulting file. [x]

### Testing Plan
- **Integration Tests:** Execute Python `httpx` flows mirroring entire daily user journeys: An Applicant applies, a Reviewer requests correction, the Applicant supplements, the Reviewer approves, the Admin generates an Audit log, verifying the log exists. [x]
- **Exception Handler Tests:** Intentionally fire bad API shapes to assert the returned error format exactly matches the `docs/api-spec.md`. [x]
- **Frontend Integration Tests:** Confirm global error toasts trigger correctly when mocking a failed 404 response. [x]

### Definition of Done
- Exceptions anywhere in the codebase reliably map to standard JSON messages. [x]
- User actions inherently cause `AuditLog` rows to append tracking behavior automatically. [x]
- Front-end smoothly indicates loading times and reacts to errors legibly. [x]
- Metric endpoints and reporting generation commands output appropriate stats and files. [x]
