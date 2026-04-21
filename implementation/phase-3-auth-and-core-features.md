## Phase 3: Auth & Core Features

### Goals
- Secure the application using JWT-based authentication.
- Implement Role-Based Access Control (RBAC).
- Enforce the required security rules like brute-force lockouts.
- Build the frontend login flows, state management, and route guards.

### Backend Implementation
1. **Password Hashing:** Implement a `security.py` utility module containing methods for `bcrypt` (or `argon2`) hash generation and verification. Include a salt implementation.
2. **JWT Configuration:** Add functions for encoding and decoding JWT tokens using the `python-jose` or `pyjwt` library. Configure token scopes and expiration (e.g., 24h).
3. **Auth Endpoints:**
   - `POST /api/v1/auth/login`: Implement logic to hash password check, reset failed login attempts on success, increment failed attempts on error, and lock accounts according to rules (≥10 in 5 min = 30min lock).
   - `POST /api/v1/auth/logout`: Blacklist the token or let the frontend destroy it statelessly.
   - `GET /api/v1/auth/me`: Decrypt token and return user profile details with masking logic based on requester role.
   - `POST /api/v1/auth/change-password` & `PUT /api/v1/auth/me`.
4. **RBAC Middleware:** Create FastAPI dependencies (e.g., `get_current_user`, `require_role(role)`) to wrap protected endpoints.
5. **System Admin User Management:** Complete the `POST /users`, `GET /users`, `PUT /users` CRUD logic from Phase 2, explicitly locking them under the `system_admin` role.

### Frontend Implementation
1. **Login & Auth State:** Create a `Login.vue` page. Implement the `authStore` in Pinia to manage login submission, store the JWT in `localStorage` or memory, and track user profile and roles.
2. **Axios Interceptors:** Extend the Axios setup to attach `Authorization: Bearer <token>` to all requests, and handle global 401s by redirecting to `/login`.
3. **Route Guards:** Add `beforeEach` navigation guards in Vue Router. Restrict routes dynamically based on `authStore.user.role`.
4. **System Admin Dashboard:** Create a `UserManagement.vue` page for creating and managing different roles.

### Testing Plan
- **Backend Auth Flow Tests:**
  - Test valid login yields an access token (`test_login_success`).
  - Test incorrect passwords (`test_login_invalid`).
  - Test brute logic: mock 10 incorrect logins, verify account lockout returns 423 status code (`test_brute_force_lockout`).
  - Test RBAC: create an applicant test token, try accessing `GET /users` (should yield 403 Forbidden).
- **Frontend Auth Tests:**
  - Mock Axios response to simulate login success and verify Pinia state updates.
  - Test route guards logically (Applicant trying to hit `/admin/users` should redirect).

### Definition of Done
- JWT tokens are effectively verified across API routes.
- Brute-force logic is active and tested.
- Accessing an authenticated frontend route without logging in redirects to `/login`.
- System administrators can successfully create roles using the User Management interface.
