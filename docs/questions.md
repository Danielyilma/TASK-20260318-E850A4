# Business Logic Questions Log

1. [Waitlist Promotion Trigger]
   - **Question**: Does the system automatically "Promote from Waitlist" when an Approved slot opens, or is it a manual Reviewer action?
   - **My Understanding**: The state machine lists it as a state, but doesn't define a "Waitlisted" entry condition or an automatic trigger.
   - **Solution**: I will implement "Waitlisted" as a manual status a Reviewer can assign. Promotion will be a manual button click on the Reviewer's list page that transitions the state to "Approved."

2. [Material Versioning Eviction]
   - **Question**: When a user uploads a 4th version of a document, how does the system handle the "up to three versions" limit?
   - **My Understanding**: The phrase "retaining up to three versions" implies the system should not store a 4th.
   - **Solution**: I will implement a First-In-First-Out (FIFO) rotation. Upon the 4th upload, the oldest version (Version 1) will be deleted from the local disk, and the new file will be saved as the current version.

3. [Supplementary Window Activation]
   - **Question**: Does the 72-hour timer for supplementary submission start from the Activity Deadline or the Reviewer's "Needs Correction" action?
   - **My Understanding**: Since it's a "correction" process, the timer should be tied to the feedback loop, not the original submission deadline.
   - **Solution**: The 72-hour countdown will begin the moment a Reviewer submits a "Needs Correction" comment. The frontend will display a "Time Remaining" clock based on this backend timestamp.

4. [Budget Baseline Source]
   - **Question**: Which field serves as the baseline for the "10% overspend" warning?
   - **My Understanding**: The registration form acts as the initial "contract," so the requested amount there should be the anchor.
   - **Solution**: The `requested_funding` field in the Registration model will be locked upon approval. All `transaction_records` will be summed and compared against `requested_funding * 1.10` to trigger the popup.

5. [Identity Masking vs. Reviewer Access]
   - **Question**: If ID numbers are masked, how can Reviewers perform "quality validation" against uploaded ID materials?
   - **My Understanding**: Security rules usually allow the "Checker" to see data that the "Accountant" cannot.
   - **Solution**: Use role-based masking in the Vue.js components. The `Financial Administrator` will see `****`, but the `Reviewer` will see the full data only when clicking a "Verify" icon, which will be recorded in the `traceable logs`.

6. [Duplicate Detection Scope]
   - **Question**: Does the SHA-256 duplicate check look for duplicates within a single application or across the entire system?
   - **My Understanding**: "Duplicate submission detection" usually prevents two different people from submitting the same document to claim the same funding.
   - **Solution**: I will check the SHA-256 fingerprint against all files in the `PostgreSQL` materials table. If a match is found anywhere in the system, the upload is rejected.