## Phase 6: Testing & Hardening

### Goals
- Bulletproof the application by assessing and locking down complex edge cases and security boundaries.
- Build the data backup mechanisms critical for the offline-first environment.
- Aim for near complete test coverage across backend and frontend domains.

### Backend Implementation [x]
1. **Security Review & Enhancements:** [x]
   - Conduct strict parameter validation reviews, preventing injection vulnerabilities.
   - Implement and thoroughly test endpoint role guards on every single route ensuring data isolation (Applicants simply cannot read other Applicants' data).
   - Ensure the `Verify Sensitive Data` endpoint successfully unmasks details when accessed by Reviewers and tracks it on the audit log.
2. **Backup & Recovery Strategy:** [x]
   - Implement APIs that trigger `pg_dump` via `subprocess` mapping to a local backup directory.
   - Capture a zip/tar of the loaded local material uploads directory.
   - Build the `POST /backups/{backup_id}/restore` endpoint that reverses the process, locking out access to the platform temporarily during execution to ensure consistency.
3. **Data Integrity Checks:** [x] Evaluate SQLAlchemy cascades; ensure deleting an item does not orphan records, or properly restrict deletion due to Foreign Key bounds.

### Frontend Implementation [x]
1. **Accessibility (a11y):** [x] Perform ARIA tag reviews. Make sure forms map to labels appropriately, and that wizard navigation works strictly using the keyboard.
2. **Edge Failure States:** [x] Design and implement fallback UI elements:
   - Behavior when the server drops offline.
   - Polished visualization when materials are fully locked due to missed deadlines.
3. **Data Polish:** [x] Map any complex frontend conditional logic matching edge-case backend responses completely.

### Testing Plan
- **Goal:** Nearing 100% backend API coverage; highly strategic frontend test sets.
- **Tools:** Use `pytest-cov` to assess untested branches in the Python codebase.
- **End-To-End (E2E) Flow Tests:** Consider playwright or Cypress (if standard) or rigorous python TestClient workflows handling the most extreme paths:
   - What happens if 54 elements are submitted to the 50 batch limit endpoint?
   - What happens if the duplicate file check happens concurrently?
- **Failure Scenario Tests:** Provide invalid data across DB connections to prove transaction rollbacks work effectively and safely in API routes.

### Definition of Done
- E2E tests fully simulate core user journey bounds with continuous success.
- Backup generation API reliably dumps SQL files directly; restore function parses them into an empty test database successfully.
- Code coverage tools evaluate an extremely high confidence level (>95%).
- App has been scrutinized manually against the requirements contained within `docs/questions.md` and `prompt.md`.
