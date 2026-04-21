# Activity Registration and Funding Audit Management Platform — API Specification

Base path: `/api/v1`

---

## Authentication

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/login` | Public | Login and issue JWT token |
| POST | `/auth/logout` | Auth | Revoke current token |
| GET | `/auth/me` | Auth | Get current authenticated user |
| PUT | `/auth/me` | Auth | Update own profile |
| POST | `/auth/change-password` | Auth | Change own password |

### Authentication Flow

- Auth is JWT bearer tokens issued by `POST /auth/login`.
- Protected endpoints require `Authorization: Bearer <token>`.
- `POST /auth/logout` invalidates the current token.
- Account is locked for 30 minutes after ≥10 failed login attempts within 5 minutes.

---

### POST `/auth/login`

Authenticate user and receive JWT token.

**Auth:** Public

**Request:**
```json
{
  "username": "john_doe",
  "password": "SecureP@ss1"
}
```

**Response (200):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "role": "applicant",
    "created_at": "2026-01-15T08:30:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2026-01-16T08:30:00Z"
}
```

**Validation:**
- `username`: required, string
- `password`: required, string

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 401 | `UNAUTHORIZED` | Invalid username or password |
| 423 | `ACCOUNT_LOCKED` | Account is locked. Try again after {locked_until} |

---

### POST `/auth/logout`

Revoke the current JWT token.

**Auth:** Required

**Request:** None (token from Authorization header)

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 401 | `UNAUTHORIZED` | Missing or invalid token |

---

### GET `/auth/me`

Get the current authenticated user's profile.

**Auth:** Required

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "role": "applicant",
  "id_number": "****",
  "contact_info": "****",
  "is_locked": false,
  "created_at": "2026-01-15T08:30:00Z",
  "updated_at": "2026-01-15T08:30:00Z"
}
```

> Note: `id_number` and `contact_info` are role-masked. Applicants see their own data unmasked. Reviewers can unmask via the verify endpoint. Financial admins always see `****`.

---

### PUT `/auth/me`

Update the current user's own profile fields.

**Auth:** Required

**Request:**
```json
{
  "contact_info": "new_email@example.com"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "role": "applicant",
  "contact_info": "new_email@example.com",
  "updated_at": "2026-03-20T14:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |

---

### POST `/auth/change-password`

Change the current user's password.

**Auth:** Required

**Request:**
```json
{
  "current_password": "OldP@ss1",
  "new_password": "NewSecureP@ss2"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Validation:**
- `current_password`: required, must match current password
- `new_password`: required, ≥8 chars, must contain uppercase, lowercase, digit, special character

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | New password does not meet complexity requirements |
| 401 | `UNAUTHORIZED` | Current password is incorrect |

---

## Users (System Admin Only)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/users` | System Admin | Create a new user account |
| GET | `/users` | System Admin | List all users |
| GET | `/users/{user_id}` | System Admin | Get user details |
| PUT | `/users/{user_id}` | System Admin | Update user |
| DELETE | `/users/{user_id}` | System Admin | Deactivate user |
| POST | `/users/{user_id}/unlock` | System Admin | Manually unlock a locked account |

---

### POST `/users`

Create a new user account. Only system administrators can create users (no self-registration).

**Auth:** System Admin

**Request:**
```json
{
  "username": "jane_reviewer",
  "password": "SecureP@ss1",
  "role": "reviewer",
  "id_number": "ID-2026-00451",
  "contact_info": "jane@example.com"
}
```

**Response (201):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "username": "jane_reviewer",
  "role": "reviewer",
  "is_locked": false,
  "created_at": "2026-03-18T10:00:00Z",
  "updated_at": "2026-03-18T10:00:00Z"
}
```

**Validation:**
- `username`: required, 3–100 chars, alphanumeric + underscore, unique
- `password`: required, ≥8 chars, must contain uppercase, lowercase, digit, special character
- `role`: required, one of `applicant`, `reviewer`, `financial_admin`, `system_admin`

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 409 | `CONFLICT` | Username already exists |
| 403 | `FORBIDDEN` | Only system administrators can create users |

---

### GET `/users`

List all users with pagination and optional filters.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `role` (string, optional): filter by role
- `is_locked` (bool, optional): filter by lock status
- `search` (string, optional): search by username

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "role": "applicant",
      "is_locked": false,
      "created_at": "2026-01-15T08:30:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### GET `/users/{user_id}`

Get a single user's details.

**Auth:** System Admin

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "role": "applicant",
  "id_number": "ID-2026-00100",
  "contact_info": "john@example.com",
  "is_locked": false,
  "failed_login_attempts": 0,
  "created_at": "2026-01-15T08:30:00Z",
  "updated_at": "2026-02-10T12:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | User not found |

---

### PUT `/users/{user_id}`

Update a user's profile.

**Auth:** System Admin

**Request:**
```json
{
  "role": "financial_admin",
  "contact_info": "john_updated@example.com"
}
```

**Response (200):** Updated user object (same schema as GET).

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 404 | `NOT_FOUND` | User not found |

---

### DELETE `/users/{user_id}`

Deactivate a user account (soft delete).

**Auth:** System Admin

**Response (200):**
```json
{
  "message": "User deactivated successfully"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | User not found |

---

### POST `/users/{user_id}/unlock`

Manually unlock a locked user account before the 30-minute window expires.

**Auth:** System Admin

**Response (200):**
```json
{
  "message": "User account unlocked successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | User not found |
| 409 | `CONFLICT` | User account is not locked |

---

## Activities (System Admin)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/activities` | System Admin | Create a new activity |
| GET | `/activities` | Auth | List activities |
| GET | `/activities/{activity_id}` | Auth | Get activity details |
| PUT | `/activities/{activity_id}` | System Admin | Update activity |
| DELETE | `/activities/{activity_id}` | System Admin | Delete activity |

---

### POST `/activities`

Create a new activity that applicants can register for.

**Auth:** System Admin

**Request:**
```json
{
  "name": "2026 Community Development Grant",
  "description": "Annual grant for community projects",
  "deadline": "2026-06-30T23:59:59Z",
  "budget": 500000.00
}
```

**Response (201):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440010",
  "name": "2026 Community Development Grant",
  "description": "Annual grant for community projects",
  "deadline": "2026-06-30T23:59:59Z",
  "budget": 500000.00,
  "is_active": true,
  "created_at": "2026-03-01T09:00:00Z",
  "updated_at": "2026-03-01T09:00:00Z"
}
```

**Validation:**
- `name`: required, 1–255 chars
- `deadline`: required, must be a future ISO 8601 timestamp
- `budget`: required, numeric, > 0

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 403 | `FORBIDDEN` | Insufficient permissions |

---

### GET `/activities`

List all activities with pagination.

**Auth:** Required (any role)

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `is_active` (bool, optional)
- `search` (string, optional): search by name

**Response (200):**
```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440010",
      "name": "2026 Community Development Grant",
      "description": "Annual grant for community projects",
      "deadline": "2026-06-30T23:59:59Z",
      "budget": 500000.00,
      "is_active": true,
      "created_at": "2026-03-01T09:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/activities/{activity_id}`

Get a single activity's details.

**Auth:** Required

**Response (200):** Single activity object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Activity not found |

---

### PUT `/activities/{activity_id}`

Update an activity.

**Auth:** System Admin

**Request:**
```json
{
  "name": "2026 Community Development Grant (Updated)",
  "deadline": "2026-07-15T23:59:59Z",
  "budget": 600000.00
}
```

**Response (200):** Updated activity object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 404 | `NOT_FOUND` | Activity not found |

---

### DELETE `/activities/{activity_id}`

Delete an activity (soft delete; cannot delete if registrations exist).

**Auth:** System Admin

**Response (200):**
```json
{
  "message": "Activity deleted successfully"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Activity not found |
| 409 | `CONFLICT` | Cannot delete activity with existing registrations |

---

## Registrations

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/registrations` | Applicant | Create a new registration |
| GET | `/registrations` | Auth + role-scoped | List registrations |
| GET | `/registrations/{registration_id}` | Auth + policy | Get registration details |
| PUT | `/registrations/{registration_id}` | Applicant owner | Update registration (draft only) |
| DELETE | `/registrations/{registration_id}` | Applicant owner | Delete registration (draft only) |
| PATCH | `/registrations/{registration_id}/submit` | Applicant owner | Submit a draft registration |
| PATCH | `/registrations/{registration_id}/cancel` | Applicant owner | Cancel a registration |

---

### POST `/registrations`

Create a new draft registration for an activity.

**Auth:** Applicant

**Request:**
```json
{
  "activity_id": "770e8400-e29b-41d4-a716-446655440010",
  "form_data": {
    "project_title": "Street Library Initiative",
    "project_description": "Setting up free libraries in underserved neighborhoods",
    "target_beneficiaries": 500,
    "start_date": "2026-08-01",
    "end_date": "2026-12-31"
  },
  "requested_funding": 25000.00
}
```

**Response (201):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440020",
  "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
  "activity_id": "770e8400-e29b-41d4-a716-446655440010",
  "form_data": {
    "project_title": "Street Library Initiative",
    "project_description": "Setting up free libraries in underserved neighborhoods",
    "target_beneficiaries": 500,
    "start_date": "2026-08-01",
    "end_date": "2026-12-31"
  },
  "requested_funding": 25000.00,
  "status": "draft",
  "deadline": "2026-06-30T23:59:59Z",
  "is_locked": false,
  "supplementary_used": false,
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-20T10:00:00Z"
}
```

**Validation:**
- `activity_id`: required, must reference an active activity with a future deadline
- `form_data`: required, object; validated against activity checklist schema
- `requested_funding`: required, numeric, > 0

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 400 | `DEADLINE_PASSED` | Activity deadline has passed |
| 404 | `NOT_FOUND` | Activity not found |

---

### GET `/registrations`

List registrations. Applicants see only their own; reviewers see all; financial admins see approved only.

**Auth:** Required (role-scoped)

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `status` (string, optional): filter by status
- `activity_id` (UUID, optional): filter by activity
- `sort` (string, optional): e.g., `-created_at`, `requested_funding`

**Response (200):**
```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440020",
      "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
      "activity_id": "770e8400-e29b-41d4-a716-446655440010",
      "status": "submitted",
      "requested_funding": 25000.00,
      "deadline": "2026-06-30T23:59:59Z",
      "is_locked": false,
      "created_at": "2026-03-20T10:00:00Z"
    }
  ],
  "total": 35,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

---

### GET `/registrations/{registration_id}`

Get a single registration's full details.

**Auth:** Required + ownership/role policy

**Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440020",
  "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
  "activity_id": "770e8400-e29b-41d4-a716-446655440010",
  "form_data": {
    "project_title": "Street Library Initiative",
    "project_description": "Setting up free libraries in underserved neighborhoods",
    "target_beneficiaries": 500,
    "start_date": "2026-08-01",
    "end_date": "2026-12-31"
  },
  "requested_funding": 25000.00,
  "status": "submitted",
  "deadline": "2026-06-30T23:59:59Z",
  "is_locked": false,
  "supplementary_used": false,
  "supplementary_requested_at": null,
  "supplementary_deadline": null,
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-20T10:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 403 | `FORBIDDEN` | You do not have access to this registration |
| 404 | `NOT_FOUND` | Registration not found |

---

### PUT `/registrations/{registration_id}`

Update a registration. Only allowed while status is `draft`.

**Auth:** Applicant owner

**Request:**
```json
{
  "form_data": {
    "project_title": "Street Library Initiative (Revised)",
    "target_beneficiaries": 750
  },
  "requested_funding": 30000.00
}
```

**Response (200):** Updated registration object.

**Validation:**
- Registration must be in `draft` status
- Deadline must not have passed
- Same field-level validations as POST

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 400 | `INVALID_STATE_TRANSITION` | Registration can only be updated in draft status |
| 400 | `DEADLINE_PASSED` | Activity deadline has passed |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Registration not found |

---

### DELETE `/registrations/{registration_id}`

Delete a registration. Only allowed while status is `draft`.

**Auth:** Applicant owner

**Response (200):**
```json
{
  "message": "Registration deleted successfully"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Only draft registrations can be deleted |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Registration not found |

---

### PATCH `/registrations/{registration_id}/submit`

Submit a draft registration, transitioning status from `draft` to `submitted`.

**Auth:** Applicant owner

**Request:** None

**Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440020",
  "status": "submitted",
  "updated_at": "2026-03-21T09:00:00Z"
}
```

**Validation:**
- Status must be `draft`
- All required checklist materials must be uploaded with status `submitted`
- Deadline must not have passed

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Registration is not in draft status |
| 400 | `VALIDATION_ERROR` | Required materials are missing |
| 400 | `DEADLINE_PASSED` | Activity deadline has passed |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Registration not found |

---

### PATCH `/registrations/{registration_id}/cancel`

Cancel a registration. Allowed from `submitted`, `supplemented`, or `waitlisted` status.

**Auth:** Applicant owner

**Request:** None

**Response (200):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440020",
  "status": "canceled",
  "updated_at": "2026-03-22T11:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Registration cannot be canceled from current status |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Registration not found |

---

## Material Checklists

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/registrations/{registration_id}/checklist` | System Admin | Add a checklist item |
| GET | `/registrations/{registration_id}/checklist` | Auth + policy | List checklist items |
| GET | `/registrations/{registration_id}/checklist/{item_id}` | Auth + policy | Get checklist item details |
| PUT | `/registrations/{registration_id}/checklist/{item_id}` | System Admin | Update checklist item |
| DELETE | `/registrations/{registration_id}/checklist/{item_id}` | System Admin | Delete checklist item |

---

### POST `/registrations/{registration_id}/checklist`

Add a material checklist item to a registration.

**Auth:** System Admin

**Request:**
```json
{
  "item_name": "Government-issued ID",
  "is_required": true,
  "allowed_types": ["pdf", "jpg", "png"],
  "max_file_size_mb": 20
}
```

**Response (201):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440030",
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "item_name": "Government-issued ID",
  "is_required": true,
  "allowed_types": ["pdf", "jpg", "png"],
  "max_file_size_mb": 20,
  "created_at": "2026-03-18T10:00:00Z"
}
```

**Validation:**
- `item_name`: required, 1–255 chars
- `allowed_types`: required, array of strings, each one of `pdf`, `jpg`, `png`
- `max_file_size_mb`: optional, int, 1–20, default 20

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 404 | `NOT_FOUND` | Registration not found |

---

### GET `/registrations/{registration_id}/checklist`

List all checklist items for a registration including upload status per item.

**Auth:** Required + ownership/role policy

**Response (200):**
```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440030",
      "item_name": "Government-issued ID",
      "is_required": true,
      "allowed_types": ["pdf", "jpg", "png"],
      "max_file_size_mb": 20,
      "versions_count": 2,
      "latest_version_label": "submitted",
      "created_at": "2026-03-18T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

### GET `/registrations/{registration_id}/checklist/{item_id}`

Get a single checklist item with all its versions.

**Auth:** Required + ownership/role policy

**Response (200):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440030",
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "item_name": "Government-issued ID",
  "is_required": true,
  "allowed_types": ["pdf", "jpg", "png"],
  "max_file_size_mb": 20,
  "versions": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440040",
      "version_number": 1,
      "file_name": "id_front.jpg",
      "file_size_bytes": 2048576,
      "file_type": "jpg",
      "sha256_hash": "a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
      "label": "submitted",
      "uploaded_at": "2026-03-20T10:30:00Z"
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440041",
      "version_number": 2,
      "file_name": "id_front_v2.jpg",
      "file_size_bytes": 1948576,
      "file_type": "jpg",
      "sha256_hash": "b4f3c9d0e2f5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "label": "submitted",
      "uploaded_at": "2026-03-21T14:00:00Z"
    }
  ],
  "created_at": "2026-03-18T10:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Checklist item not found |

---

### PUT `/registrations/{registration_id}/checklist/{item_id}`

Update a checklist item configuration.

**Auth:** System Admin

**Request:**
```json
{
  "item_name": "Government-issued ID (front and back)",
  "is_required": true,
  "allowed_types": ["pdf", "jpg", "png"],
  "max_file_size_mb": 15
}
```

**Response (200):** Updated checklist item object.

---

### DELETE `/registrations/{registration_id}/checklist/{item_id}`

Delete a checklist item (only if no versions uploaded).

**Auth:** System Admin

**Response (200):**
```json
{
  "message": "Checklist item deleted successfully"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Checklist item not found |
| 409 | `CONFLICT` | Cannot delete checklist item with uploaded materials |

---

## Materials (File Upload/Download)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/registrations/{registration_id}/materials/{item_id}/upload` | Applicant owner | Upload a material file |
| GET | `/registrations/{registration_id}/materials/{item_id}/versions` | Auth + policy | List all versions of a material |
| GET | `/materials/{version_id}/download` | Auth + policy | Download a material file |
| PATCH | `/registrations/{registration_id}/materials/{item_id}/versions/{version_id}/label` | Applicant owner | Update version label |

---

### POST `/registrations/{registration_id}/materials/{item_id}/upload`

Upload a file for a checklist item. If 3 versions exist, the oldest is evicted (FIFO). SHA-256 hash is computed and checked system-wide for duplicates.

**Auth:** Applicant owner

**Request:** `multipart/form-data`
- `file`: the file to upload (required)

**Response (201):**
```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440050",
  "checklist_item_id": "990e8400-e29b-41d4-a716-446655440030",
  "version_number": 3,
  "file_name": "id_front_v3.jpg",
  "file_size_bytes": 1850000,
  "file_type": "jpg",
  "sha256_hash": "c5f4d0e1f3a6b8c9d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4",
  "label": "pending_submission",
  "uploaded_at": "2026-03-22T09:00:00Z",
  "evicted_version": {
    "id": "aa0e8400-e29b-41d4-a716-446655440040",
    "version_number": 1,
    "file_name": "id_front.jpg"
  }
}
```

**Validation:**
- File type must be in checklist item's `allowed_types`
- Single file ≤ 20MB
- Total upload for registration ≤ 200MB
- SHA-256 hash must not exist anywhere in the system
- Registration must not be locked (deadline not passed, or within supplementary window)
- If supplementary window: `supplementary_used` must be false, and `supplementary_deadline` must be in the future

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `FILE_TYPE_NOT_ALLOWED` | File type '{type}' is not allowed. Accepted: {allowed_types} |
| 400 | `FILE_TOO_LARGE` | File size exceeds 20MB limit |
| 400 | `FILE_TOO_LARGE` | Total upload size for this registration exceeds 200MB |
| 400 | `DUPLICATE_FILE` | This file has already been uploaded in the system (SHA-256 match) |
| 400 | `DEADLINE_PASSED` | Upload deadline has passed |
| 400 | `SUPPLEMENTARY_EXHAUSTED` | Supplementary submission has already been used |
| 400 | `SUPPLEMENTARY_EXPIRED` | The 72-hour supplementary window has expired |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Registration or checklist item not found |

---

### GET `/registrations/{registration_id}/materials/{item_id}/versions`

List all versions of a material for a checklist item.

**Auth:** Required + ownership/role policy

**Response (200):**
```json
{
  "checklist_item_id": "990e8400-e29b-41d4-a716-446655440030",
  "item_name": "Government-issued ID",
  "versions": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440041",
      "version_number": 2,
      "file_name": "id_front_v2.jpg",
      "file_size_bytes": 1948576,
      "file_type": "jpg",
      "sha256_hash": "b4f3c9d0e2f5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "label": "submitted",
      "uploaded_at": "2026-03-21T14:00:00Z"
    },
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440050",
      "version_number": 3,
      "file_name": "id_front_v3.jpg",
      "file_size_bytes": 1850000,
      "file_type": "jpg",
      "sha256_hash": "c5f4d0e1f3a6b8c9d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4",
      "label": "pending_submission",
      "uploaded_at": "2026-03-22T09:00:00Z"
    }
  ]
}
```

---

### GET `/materials/{version_id}/download`

Download a specific material version file.

**Auth:** Required + ownership/role policy

**Response (200):** Binary file stream with appropriate `Content-Type` and `Content-Disposition` headers.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 403 | `FORBIDDEN` | You do not have access to this material |
| 404 | `NOT_FOUND` | Material version not found |

---

### PATCH `/registrations/{registration_id}/materials/{item_id}/versions/{version_id}/label`

Update the label of a material version.

**Auth:** Applicant owner

**Request:**
```json
{
  "label": "submitted"
}
```

**Response (200):**
```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440050",
  "label": "submitted",
  "updated_at": "2026-03-22T10:00:00Z"
}
```

**Validation:**
- `label`: required, one of `pending_submission`, `submitted`, `needs_correction`

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | Invalid label value |
| 403 | `FORBIDDEN` | You do not own this registration |
| 404 | `NOT_FOUND` | Material version not found |

---

## Reviews

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| PATCH | `/registrations/{registration_id}/review` | Reviewer | Perform a single review action (state transition) |
| POST | `/reviews/batch` | Reviewer | Batch review multiple registrations |
| GET | `/registrations/{registration_id}/reviews` | Auth + policy | List review history for a registration |
| GET | `/registrations/{registration_id}/reviews/{review_id}` | Auth + policy | Get a single review record |
| PATCH | `/registrations/{registration_id}/waitlist-promote` | Reviewer | Promote a waitlisted registration to approved |

---

### PATCH `/registrations/{registration_id}/review`

Perform a review action on a single registration, transitioning its status.

**Auth:** Reviewer

**Request:**
```json
{
  "action": "approve",
  "comment": "All materials verified. Project meets criteria."
}
```

Available `action` values and their transitions:

| Action | Valid From Status | New Status |
| --- | --- | --- |
| `approve` | `submitted`, `supplemented` | `approved` |
| `reject` | `submitted`, `supplemented` | `rejected` |
| `request_correction` | `submitted`, `supplemented` | `needs_correction`* |
| `waitlist` | `submitted`, `supplemented` | `waitlisted` |
| `cancel` | `submitted`, `supplemented`, `waitlisted` | `canceled` |

*When `action` is `request_correction`, `correction_reason` is required and the 72-hour supplementary window is activated.

**Request (correction example):**
```json
{
  "action": "request_correction",
  "comment": "ID document is blurry",
  "correction_reason": "Government-issued ID is not legible. Please re-upload a clear scan."
}
```

**Response (200):**
```json
{
  "review_id": "dd0e8400-e29b-41d4-a716-446655440060",
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "reviewer_id": "660e8400-e29b-41d4-a716-446655440001",
  "previous_status": "submitted",
  "new_status": "approved",
  "comment": "All materials verified. Project meets criteria.",
  "created_at": "2026-04-01T14:30:00Z"
}
```

**Validation:**
- `action`: required, must be a valid action for the current status
- `comment`: optional (but recommended), text
- `correction_reason`: required when `action` is `request_correction`

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Cannot perform '{action}' on registration with status '{status}' |
| 400 | `VALIDATION_ERROR` | correction_reason is required for request_correction action |
| 403 | `FORBIDDEN` | Only reviewers can perform reviews |
| 404 | `NOT_FOUND` | Registration not found |

---

### POST `/reviews/batch`

Perform the same review action on multiple registrations at once. Maximum 50 registrations per batch.

**Auth:** Reviewer

**Request:**
```json
{
  "registration_ids": [
    "880e8400-e29b-41d4-a716-446655440020",
    "880e8400-e29b-41d4-a716-446655440021",
    "880e8400-e29b-41d4-a716-446655440022"
  ],
  "action": "approve",
  "comment": "Batch approved — all criteria met."
}
```

**Response (200):**
```json
{
  "batch_id": "ee0e8400-e29b-41d4-a716-446655440070",
  "total_requested": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "registration_id": "880e8400-e29b-41d4-a716-446655440020",
      "status": "success",
      "new_status": "approved",
      "review_id": "dd0e8400-e29b-41d4-a716-446655440060"
    },
    {
      "registration_id": "880e8400-e29b-41d4-a716-446655440021",
      "status": "success",
      "new_status": "approved",
      "review_id": "dd0e8400-e29b-41d4-a716-446655440061"
    },
    {
      "registration_id": "880e8400-e29b-41d4-a716-446655440022",
      "status": "success",
      "new_status": "approved",
      "review_id": "dd0e8400-e29b-41d4-a716-446655440062"
    }
  ]
}
```

**Validation:**
- `registration_ids`: required, array of UUIDs, length 1–50
- `action`: required, same values as single review
- All registrations must be in a valid source status for the action

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `BATCH_SIZE_EXCEEDED` | Maximum 50 registrations per batch |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 403 | `FORBIDDEN` | Only reviewers can perform batch reviews |

> Note: Partially successful batches return 200 with individual results. Each failed registration includes the error reason in its result entry.

---

### GET `/registrations/{registration_id}/reviews`

List the full review history (traceable logs) for a registration.

**Auth:** Required + ownership/role policy

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)

**Response (200):**
```json
{
  "items": [
    {
      "id": "dd0e8400-e29b-41d4-a716-446655440060",
      "reviewer_id": "660e8400-e29b-41d4-a716-446655440001",
      "reviewer_username": "jane_reviewer",
      "previous_status": "submitted",
      "new_status": "approved",
      "comment": "All materials verified.",
      "correction_reason": null,
      "batch_id": null,
      "created_at": "2026-04-01T14:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/registrations/{registration_id}/reviews/{review_id}`

Get a single review record.

**Auth:** Required + ownership/role policy

**Response (200):** Single review record object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Review record not found |

---

### PATCH `/registrations/{registration_id}/waitlist-promote`

Manually promote a waitlisted registration to approved.

**Auth:** Reviewer

**Request:**
```json
{
  "comment": "Slot opened — promoting from waitlist."
}
```

**Response (200):**
```json
{
  "review_id": "dd0e8400-e29b-41d4-a716-446655440065",
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "previous_status": "waitlisted",
  "new_status": "approved",
  "comment": "Slot opened — promoting from waitlist.",
  "created_at": "2026-04-05T09:00:00Z"
}
```

**Validation:**
- Registration must be in `waitlisted` status

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Registration is not in waitlisted status |
| 403 | `FORBIDDEN` | Only reviewers can promote from waitlist |
| 404 | `NOT_FOUND` | Registration not found |

---

## Sensitive Data Verification

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/registrations/{registration_id}/verify-sensitive` | Reviewer | Unmask sensitive fields for verification |

---

### GET `/registrations/{registration_id}/verify-sensitive`

Retrieve unmasked sensitive fields (ID number, contact info) for a registration's applicant. This action is logged in the audit trail.

**Auth:** Reviewer

**Response (200):**
```json
{
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "applicant_id": "550e8400-e29b-41d4-a716-446655440000",
  "id_number": "ID-2026-00100",
  "contact_info": "john@example.com",
  "verified_at": "2026-04-01T14:35:00Z",
  "audit_log_id": "ff0e8400-e29b-41d4-a716-446655440080"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 403 | `FORBIDDEN` | Only reviewers can verify sensitive data |
| 404 | `NOT_FOUND` | Registration not found |

---

## Funding Accounts

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/registrations/{registration_id}/funding` | Financial Admin / System Admin | Get funding account for a registration |
| GET | `/funding-accounts` | Financial Admin / System Admin | List all funding accounts |
| GET | `/funding-accounts/{account_id}` | Financial Admin / System Admin | Get funding account details |

> Funding accounts are auto-created when a registration transitions to `approved`. No manual POST is needed.

---

### GET `/registrations/{registration_id}/funding`

Get the funding account for an approved registration.

**Auth:** Financial Admin / System Admin

**Response (200):**
```json
{
  "id": "110e8400-e29b-41d4-a716-446655440090",
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "approved_budget": 25000.00,
  "total_income": 25000.00,
  "total_expenses": 18500.00,
  "balance": 6500.00,
  "is_overspent": false,
  "overspend_percentage": 0.0,
  "created_at": "2026-04-01T14:30:00Z",
  "updated_at": "2026-04-10T16:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 403 | `FORBIDDEN` | Only financial administrators can access funding accounts |
| 404 | `NOT_FOUND` | Registration or funding account not found |

---

### GET `/funding-accounts`

List all funding accounts with pagination and filters.

**Auth:** Financial Admin / System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `is_overspent` (bool, optional)
- `activity_id` (UUID, optional)

**Response (200):**
```json
{
  "items": [
    {
      "id": "110e8400-e29b-41d4-a716-446655440090",
      "registration_id": "880e8400-e29b-41d4-a716-446655440020",
      "approved_budget": 25000.00,
      "total_income": 25000.00,
      "total_expenses": 18500.00,
      "balance": 6500.00,
      "is_overspent": false,
      "created_at": "2026-04-01T14:30:00Z"
    }
  ],
  "total": 20,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/funding-accounts/{account_id}`

Get a single funding account by ID.

**Auth:** Financial Admin / System Admin

**Response (200):** Full funding account object (same schema as GET by registration).

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Funding account not found |

---

## Transactions

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/funding-accounts/{account_id}/transactions` | Financial Admin | Record a transaction |
| GET | `/funding-accounts/{account_id}/transactions` | Financial Admin / System Admin | List transactions |
| GET | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Financial Admin / System Admin | Get transaction details |
| PUT | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Financial Admin | Update a transaction |
| DELETE | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Financial Admin | Delete a transaction |
| POST | `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice` | Financial Admin | Upload invoice attachment |
| GET | `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice` | Financial Admin / System Admin | Download invoice attachment |

---

### POST `/funding-accounts/{account_id}/transactions`

Record an income or expense transaction. If the expense causes `total_expenses > approved_budget × 1.10`, the response includes an `overspend_warning` and requires confirmation.

**Auth:** Financial Admin

**Request:**
```json
{
  "type": "expense",
  "amount": 5000.00,
  "category": "Equipment",
  "description": "Bookshelves for two library locations"
}
```

**Response (201) — Normal:**
```json
{
  "id": "220e8400-e29b-41d4-a716-446655440100",
  "funding_account_id": "110e8400-e29b-41d4-a716-446655440090",
  "type": "expense",
  "amount": 5000.00,
  "category": "Equipment",
  "description": "Bookshelves for two library locations",
  "recorded_by": "770e8400-e29b-41d4-a716-446655440002",
  "created_at": "2026-04-10T16:00:00Z"
}
```

**Response (200) — Overspend Warning:**
```json
{
  "overspend_warning": true,
  "current_total_expenses": 26500.00,
  "approved_budget": 25000.00,
  "overspend_percentage": 6.0,
  "threshold": 10.0,
  "message": "This transaction would bring total expenses to 106% of the approved budget. Secondary confirmation required.",
  "pending_transaction": {
    "type": "expense",
    "amount": 5000.00,
    "category": "Equipment",
    "description": "Bookshelves for two library locations"
  },
  "confirmation_required": true
}
```

> When `overspend_warning` is true, the client must re-submit with `override_confirmed: true`:

**Request (confirmation):**
```json
{
  "type": "expense",
  "amount": 5000.00,
  "category": "Equipment",
  "description": "Bookshelves for two library locations",
  "override_confirmed": true
}
```

**Response (201) — With override:** Same as normal, with additional field:
```json
{
  "id": "220e8400-e29b-41d4-a716-446655440100",
  "type": "expense",
  "amount": 5000.00,
  "category": "Equipment",
  "description": "Bookshelves for two library locations",
  "override_confirmed": true,
  "overspend_percentage": 6.0,
  "recorded_by": "770e8400-e29b-41d4-a716-446655440002",
  "created_at": "2026-04-10T16:00:00Z"
}
```

**Validation:**
- `type`: required, one of `income`, `expense`
- `amount`: required, numeric, > 0
- `category`: required, non-empty string
- `override_confirmed`: required when expense would exceed 110% of budget

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 403 | `FORBIDDEN` | Only financial administrators can record transactions |
| 403 | `OVERSPEND_CONFIRMATION_REQUIRED` | Transaction exceeds 110% budget threshold. Re-submit with override_confirmed |
| 404 | `NOT_FOUND` | Funding account not found |

---

### GET `/funding-accounts/{account_id}/transactions`

List all transactions for a funding account with pagination and filters.

**Auth:** Financial Admin / System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `type` (string, optional): `income` or `expense`
- `category` (string, optional): filter by category
- `start_date` (ISO 8601, optional): filter from date
- `end_date` (ISO 8601, optional): filter to date
- `sort` (string, optional): e.g., `-created_at`, `amount`

**Response (200):**
```json
{
  "items": [
    {
      "id": "220e8400-e29b-41d4-a716-446655440100",
      "type": "expense",
      "amount": 5000.00,
      "category": "Equipment",
      "description": "Bookshelves for two library locations",
      "invoice_file_path": null,
      "recorded_by": "770e8400-e29b-41d4-a716-446655440002",
      "created_at": "2026-04-10T16:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/funding-accounts/{account_id}/transactions/{transaction_id}`

Get a single transaction's details.

**Auth:** Financial Admin / System Admin

**Response (200):** Full transaction object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Transaction not found |

---

### PUT `/funding-accounts/{account_id}/transactions/{transaction_id}`

Update a transaction record.

**Auth:** Financial Admin

**Request:**
```json
{
  "amount": 5500.00,
  "description": "Bookshelves for three library locations (corrected)"
}
```

**Response (200):** Updated transaction object.

**Validation:** Same as POST. Overspend check is re-evaluated on update.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |
| 403 | `OVERSPEND_CONFIRMATION_REQUIRED` | Updated amount exceeds 110% budget threshold |
| 404 | `NOT_FOUND` | Transaction not found |

---

### DELETE `/funding-accounts/{account_id}/transactions/{transaction_id}`

Delete a transaction record.

**Auth:** Financial Admin

**Response (200):**
```json
{
  "message": "Transaction deleted successfully"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Transaction not found |

---

### POST `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice`

Upload an invoice attachment for a transaction.

**Auth:** Financial Admin

**Request:** `multipart/form-data`
- `file`: invoice file (PDF/JPG/PNG, ≤ 20MB)

**Response (201):**
```json
{
  "transaction_id": "220e8400-e29b-41d4-a716-446655440100",
  "invoice_file_name": "invoice_equipment_001.pdf",
  "invoice_file_size_bytes": 524288,
  "uploaded_at": "2026-04-10T16:30:00Z"
}
```

**Validation:**
- File type: PDF, JPG, or PNG
- File size: ≤ 20MB

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `FILE_TYPE_NOT_ALLOWED` | Invoice must be PDF, JPG, or PNG |
| 400 | `FILE_TOO_LARGE` | Invoice file size exceeds 20MB |
| 404 | `NOT_FOUND` | Transaction not found |

---

### GET `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice`

Download the invoice attachment for a transaction.

**Auth:** Financial Admin / System Admin

**Response (200):** Binary file stream.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Invoice not found for this transaction |

---

## Financial Statistics

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/statistics/funding` | Financial Admin / System Admin | Get funding statistics by category and time |
| GET | `/statistics/funding/{account_id}` | Financial Admin / System Admin | Get statistics for a single funding account |

---

### GET `/statistics/funding`

Get aggregated financial statistics across all funding accounts.

**Auth:** Financial Admin / System Admin

**Query Parameters:**
- `activity_id` (UUID, optional): scope to an activity
- `category` (string, optional): filter by transaction category
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)
- `group_by` (string, optional): `category`, `month`, `quarter` (default: `category`)

**Response (200):**
```json
{
  "summary": {
    "total_accounts": 20,
    "total_approved_budget": 500000.00,
    "total_income": 450000.00,
    "total_expenses": 320000.00,
    "total_balance": 130000.00,
    "overspent_accounts": 2,
    "overspending_rate": 10.0
  },
  "by_category": [
    {
      "category": "Equipment",
      "total_income": 0.00,
      "total_expenses": 85000.00,
      "transaction_count": 15
    },
    {
      "category": "Personnel",
      "total_income": 0.00,
      "total_expenses": 120000.00,
      "transaction_count": 30
    }
  ],
  "by_time": [
    {
      "period": "2026-03",
      "total_income": 200000.00,
      "total_expenses": 150000.00,
      "transaction_count": 45
    },
    {
      "period": "2026-04",
      "total_income": 250000.00,
      "total_expenses": 170000.00,
      "transaction_count": 38
    }
  ]
}
```

---

### GET `/statistics/funding/{account_id}`

Get statistics for a single funding account.

**Auth:** Financial Admin / System Admin

**Response (200):**
```json
{
  "account_id": "110e8400-e29b-41d4-a716-446655440090",
  "approved_budget": 25000.00,
  "total_income": 25000.00,
  "total_expenses": 18500.00,
  "balance": 6500.00,
  "overspend_percentage": 0.0,
  "is_overspent": false,
  "by_category": [
    {
      "category": "Equipment",
      "total_expenses": 10000.00,
      "transaction_count": 3
    },
    {
      "category": "Personnel",
      "total_expenses": 8500.00,
      "transaction_count": 5
    }
  ]
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Funding account not found |

---

## Quality Metrics

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/metrics/quality` | System Admin | Get quality metrics (approval rate, correction rate, overspending rate) |
| GET | `/metrics/quality/{activity_id}` | System Admin | Get quality metrics for a specific activity |

---

### GET `/metrics/quality`

Get system-wide quality metrics.

**Auth:** System Admin

**Query Parameters:**
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)

**Response (200):**
```json
{
  "total_registrations": 150,
  "total_reviewed": 120,
  "approved": 85,
  "rejected": 20,
  "needs_correction": 10,
  "waitlisted": 5,
  "approval_rate": 70.83,
  "correction_rate": 8.33,
  "overspending_rate": 10.0,
  "computed_at": "2026-04-15T12:00:00Z"
}
```

---

### GET `/metrics/quality/{activity_id}`

Get quality metrics for a specific activity.

**Auth:** System Admin

**Response (200):** Same schema as system-wide, scoped to the activity.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Activity not found |

---

## Alerts

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/alerts` | System Admin | List all alerts |
| GET | `/alerts/{alert_id}` | System Admin | Get alert details |
| PATCH | `/alerts/{alert_id}/acknowledge` | System Admin | Acknowledge an alert |

---

### GET `/alerts`

List alerts with pagination and filters.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `severity` (string, optional): `info`, `warning`, `critical`
- `acknowledged` (bool, optional)
- `alert_type` (string, optional)

**Response (200):**
```json
{
  "items": [
    {
      "id": "330e8400-e29b-41d4-a716-446655440110",
      "alert_type": "overspend_warning",
      "severity": "warning",
      "message": "Funding account for registration 880e... has exceeded 110% of approved budget",
      "resource_type": "funding_account",
      "resource_id": "110e8400-e29b-41d4-a716-446655440090",
      "acknowledged": false,
      "created_at": "2026-04-10T16:00:00Z"
    }
  ],
  "total": 8,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

### GET `/alerts/{alert_id}`

Get a single alert's details.

**Auth:** System Admin

**Response (200):** Full alert object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Alert not found |

---

### PATCH `/alerts/{alert_id}/acknowledge`

Acknowledge an alert.

**Auth:** System Admin

**Response (200):**
```json
{
  "id": "330e8400-e29b-41d4-a716-446655440110",
  "acknowledged": true,
  "acknowledged_by": "550e8400-e29b-41d4-a716-446655440000",
  "acknowledged_at": "2026-04-10T17:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Alert not found |
| 409 | `CONFLICT` | Alert already acknowledged |

---

## Audit Logs

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/audit-logs` | System Admin | List audit logs |
| GET | `/audit-logs/{log_id}` | System Admin | Get audit log details |

---

### GET `/audit-logs`

List audit logs with comprehensive filtering.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `user_id` (UUID, optional)
- `action` (string, optional): e.g., `login`, `review`, `upload`, `transaction`
- `resource_type` (string, optional)
- `resource_id` (UUID, optional)
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)
- `sort` (string, optional): default `-created_at`

**Response (200):**
```json
{
  "items": [
    {
      "id": "440e8400-e29b-41d4-a716-446655440120",
      "user_id": "660e8400-e29b-41d4-a716-446655440001",
      "username": "jane_reviewer",
      "action": "review",
      "resource_type": "registration",
      "resource_id": "880e8400-e29b-41d4-a716-446655440020",
      "details": {
        "previous_status": "submitted",
        "new_status": "approved"
      },
      "ip_address": "192.168.1.100",
      "created_at": "2026-04-01T14:30:00Z"
    }
  ],
  "total": 500,
  "page": 1,
  "per_page": 20,
  "pages": 25
}
```

---

### GET `/audit-logs/{log_id}`

Get a single audit log entry.

**Auth:** System Admin

**Response (200):** Full audit log object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Audit log not found |

---

## Data Collection Batches

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/data-collection/batches` | System Admin | Create a data collection batch |
| GET | `/data-collection/batches` | System Admin | List batches |
| GET | `/data-collection/batches/{batch_id}` | System Admin | Get batch details |
| PATCH | `/data-collection/batches/{batch_id}/execute` | System Admin | Execute a batch validation |
| GET | `/data-collection/batches/{batch_id}/results` | System Admin | Get validation results |

---

### POST `/data-collection/batches`

Create a data collection batch with whitelist scope rules.

**Auth:** System Admin

**Request:**
```json
{
  "name": "Q1 2026 Validation Batch",
  "scope_whitelist": {
    "activity_ids": ["770e8400-e29b-41d4-a716-446655440010"],
    "statuses": ["submitted", "supplemented"],
    "validation_types": ["type_check", "range_check", "mandatory_check"]
  }
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440130",
  "name": "Q1 2026 Validation Batch",
  "scope_whitelist": {
    "activity_ids": ["770e8400-e29b-41d4-a716-446655440010"],
    "statuses": ["submitted", "supplemented"],
    "validation_types": ["type_check", "range_check", "mandatory_check"]
  },
  "status": "pending",
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-15T09:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | {field}: {reason} |

---

### GET `/data-collection/batches`

List all data collection batches.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `status` (string, optional): `pending`, `in_progress`, `completed`, `failed`

**Response (200):** Paginated list of batch objects.

---

### GET `/data-collection/batches/{batch_id}`

Get a single batch's details.

**Auth:** System Admin

**Response (200):** Full batch object.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Batch not found |

---

### PATCH `/data-collection/batches/{batch_id}/execute`

Execute the batch validation. Runs rule-based validation (type, range, mandatory field checks) on registrations matching the whitelist scope.

**Auth:** System Admin

**Response (200):**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440130",
  "status": "completed",
  "total_validated": 35,
  "valid": 30,
  "invalid": 5,
  "completed_at": "2026-04-15T09:05:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 400 | `INVALID_STATE_TRANSITION` | Batch is not in pending status |
| 404 | `NOT_FOUND` | Batch not found |

---

### GET `/data-collection/batches/{batch_id}/results`

Get validation results for a batch.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `is_valid` (bool, optional)

**Response (200):**
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440140",
      "batch_id": "550e8400-e29b-41d4-a716-446655440130",
      "registration_id": "880e8400-e29b-41d4-a716-446655440020",
      "validation_type": "mandatory_check",
      "is_valid": false,
      "error_details": "Missing required material: Government-issued ID",
      "created_at": "2026-04-15T09:03:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

---

## Duplicate Check (Reserved)

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/similarity/check` | System Admin | Reserved similarity/duplicate check interface (disabled) |

---

### POST `/similarity/check`

Reserved endpoint for similarity/duplicate checking. Disabled by default, returns 501.

**Auth:** System Admin

**Request:**
```json
{
  "registration_id": "880e8400-e29b-41d4-a716-446655440020",
  "check_type": "content_similarity"
}
```

**Response (501):**
```json
{
  "error": {
    "code": "NOT_IMPLEMENTED",
    "message": "Similarity/duplicate check is reserved but currently disabled"
  }
}
```

---

## Reports & Exports

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/reports/reconciliation` | Financial Admin / System Admin | Generate reconciliation report |
| POST | `/reports/audit` | System Admin | Generate audit report |
| POST | `/reports/compliance` | System Admin | Generate compliance report |
| GET | `/reports` | System Admin / Financial Admin | List generated reports |
| GET | `/reports/{report_id}/download` | System Admin / Financial Admin | Download a generated report |

---

### POST `/reports/reconciliation`

Generate a financial reconciliation report.

**Auth:** Financial Admin / System Admin

**Request:**
```json
{
  "activity_id": "770e8400-e29b-41d4-a716-446655440010",
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-04-15T23:59:59Z",
  "format": "xlsx"
}
```

**Response (201):**
```json
{
  "report_id": "770e8400-e29b-41d4-a716-446655440150",
  "report_type": "reconciliation",
  "status": "completed",
  "file_name": "reconciliation_2026-01_to_2026-04.xlsx",
  "file_size_bytes": 102400,
  "created_at": "2026-04-15T10:00:00Z"
}
```

**Validation:**
- `format`: required, one of `xlsx`, `csv`, `pdf`
- `start_date` / `end_date`: optional ISO 8601 dates

---

### POST `/reports/audit`

Generate an audit trail report.

**Auth:** System Admin

**Request:**
```json
{
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-04-15T23:59:59Z",
  "user_id": null,
  "action_filter": null,
  "format": "pdf"
}
```

**Response (201):** Same schema as reconciliation report with `report_type: "audit"`.

---

### POST `/reports/compliance`

Generate a compliance report.

**Auth:** System Admin

**Request:**
```json
{
  "activity_id": "770e8400-e29b-41d4-a716-446655440010",
  "format": "pdf"
}
```

**Response (201):** Same schema as reconciliation report with `report_type: "compliance"`.

---

### GET `/reports`

List all generated reports.

**Auth:** System Admin / Financial Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `report_type` (string, optional): `reconciliation`, `audit`, `compliance`
- `format` (string, optional): `xlsx`, `csv`, `pdf`

**Response (200):** Paginated list of report objects.

---

### GET `/reports/{report_id}/download`

Download a generated report file.

**Auth:** System Admin / Financial Admin (owner or admin)

**Response (200):** Binary file stream.

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Report not found |

---

## Backups

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/backups` | System Admin | List backup records |
| POST | `/backups` | System Admin | Trigger a manual backup |
| POST | `/backups/{backup_id}/restore` | System Admin | Restore from a backup (one-click recovery) |

---

### GET `/backups`

List all backup records.

**Auth:** System Admin

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `status` (string, optional): `completed`, `failed`
- `backup_type` (string, optional): `daily_auto`, `manual`

**Response (200):**
```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440160",
      "backup_type": "daily_auto",
      "backup_path": "/backups/2026-04-15_daily.tar.gz",
      "size_bytes": 52428800,
      "status": "completed",
      "created_at": "2026-04-15T02:00:00Z",
      "restored_at": null
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 20,
  "pages": 2
}
```

---

### POST `/backups`

Trigger a manual backup.

**Auth:** System Admin

**Request:** None

**Response (201):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440170",
  "backup_type": "manual",
  "status": "completed",
  "backup_path": "/backups/2026-04-15_manual_1430.tar.gz",
  "size_bytes": 52428800,
  "created_at": "2026-04-15T14:30:00Z"
}
```

---

### POST `/backups/{backup_id}/restore`

Restore the system from a backup (one-click recovery).

**Auth:** System Admin

**Request:** None

**Response (200):**
```json
{
  "message": "System restored successfully from backup",
  "backup_id": "880e8400-e29b-41d4-a716-446655440160",
  "restored_at": "2026-04-15T15:00:00Z"
}
```

**Errors:**

| Status | Code | Message |
| --- | --- | --- |
| 404 | `NOT_FOUND` | Backup not found |
| 400 | `VALIDATION_ERROR` | Backup status is 'failed' and cannot be restored |

---

## Error Standard

All error responses follow this format:

```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human-readable description of the error"
  }
}
```

### Complete Error Code Reference

| HTTP Status | Code | Description |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | Request body or parameters failed validation |
| 400 | `INVALID_STATE_TRANSITION` | Action not allowed for current resource state |
| 400 | `DUPLICATE_FILE` | SHA-256 hash already exists system-wide |
| 400 | `FILE_TYPE_NOT_ALLOWED` | Uploaded file type not in allowed list |
| 400 | `FILE_TOO_LARGE` | File exceeds size limit (20MB single / 200MB total) |
| 400 | `DEADLINE_PASSED` | Submission deadline has passed |
| 400 | `SUPPLEMENTARY_EXHAUSTED` | One-time supplementary already used |
| 400 | `SUPPLEMENTARY_EXPIRED` | 72-hour supplementary window expired |
| 400 | `BATCH_SIZE_EXCEEDED` | Batch review exceeds 50 items |
| 400 | `BUDGET_LOCKED` | Cannot modify locked approved budget |
| 401 | `UNAUTHORIZED` | Missing, invalid, or expired token |
| 403 | `FORBIDDEN` | Insufficient role or permission |
| 403 | `OVERSPEND_CONFIRMATION_REQUIRED` | Expense exceeds 110% threshold, needs confirmation |
| 404 | `NOT_FOUND` | Requested resource does not exist |
| 409 | `CONFLICT` | Resource state conflict (e.g., duplicate username) |
| 423 | `ACCOUNT_LOCKED` | Account locked due to brute-force protection |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 501 | `NOT_IMPLEMENTED` | Reserved feature is disabled |

---

## Endpoint Summary Table

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/login` | Public | Login |
| POST | `/auth/logout` | Auth | Logout |
| GET | `/auth/me` | Auth | Get current user |
| PUT | `/auth/me` | Auth | Update own profile |
| POST | `/auth/change-password` | Auth | Change own password |
| POST | `/users` | System Admin | Create user |
| GET | `/users` | System Admin | List users |
| GET | `/users/{user_id}` | System Admin | Get user |
| PUT | `/users/{user_id}` | System Admin | Update user |
| DELETE | `/users/{user_id}` | System Admin | Deactivate user |
| POST | `/users/{user_id}/unlock` | System Admin | Unlock user |
| POST | `/activities` | System Admin | Create activity |
| GET | `/activities` | Auth | List activities |
| GET | `/activities/{activity_id}` | Auth | Get activity |
| PUT | `/activities/{activity_id}` | System Admin | Update activity |
| DELETE | `/activities/{activity_id}` | System Admin | Delete activity |
| POST | `/registrations` | Applicant | Create registration |
| GET | `/registrations` | Auth (scoped) | List registrations |
| GET | `/registrations/{registration_id}` | Auth + policy | Get registration |
| PUT | `/registrations/{registration_id}` | Applicant owner | Update registration |
| DELETE | `/registrations/{registration_id}` | Applicant owner | Delete registration |
| PATCH | `/registrations/{registration_id}/submit` | Applicant owner | Submit registration |
| PATCH | `/registrations/{registration_id}/cancel` | Applicant owner | Cancel registration |
| POST | `/registrations/{registration_id}/checklist` | System Admin | Add checklist item |
| GET | `/registrations/{registration_id}/checklist` | Auth + policy | List checklist |
| GET | `/registrations/{registration_id}/checklist/{item_id}` | Auth + policy | Get checklist item |
| PUT | `/registrations/{registration_id}/checklist/{item_id}` | System Admin | Update checklist item |
| DELETE | `/registrations/{registration_id}/checklist/{item_id}` | System Admin | Delete checklist item |
| POST | `/registrations/{registration_id}/materials/{item_id}/upload` | Applicant owner | Upload material |
| GET | `/registrations/{registration_id}/materials/{item_id}/versions` | Auth + policy | List material versions |
| GET | `/materials/{version_id}/download` | Auth + policy | Download material |
| PATCH | `/registrations/{registration_id}/materials/{item_id}/versions/{version_id}/label` | Applicant owner | Update material label |
| PATCH | `/registrations/{registration_id}/review` | Reviewer | Review registration |
| POST | `/reviews/batch` | Reviewer | Batch review |
| GET | `/registrations/{registration_id}/reviews` | Auth + policy | List review history |
| GET | `/registrations/{registration_id}/reviews/{review_id}` | Auth + policy | Get review record |
| PATCH | `/registrations/{registration_id}/waitlist-promote` | Reviewer | Promote from waitlist |
| GET | `/registrations/{registration_id}/verify-sensitive` | Reviewer | Unmask sensitive data |
| GET | `/registrations/{registration_id}/funding` | Fin Admin / Admin | Get funding account |
| GET | `/funding-accounts` | Fin Admin / Admin | List funding accounts |
| GET | `/funding-accounts/{account_id}` | Fin Admin / Admin | Get funding account |
| POST | `/funding-accounts/{account_id}/transactions` | Fin Admin | Record transaction |
| GET | `/funding-accounts/{account_id}/transactions` | Fin Admin / Admin | List transactions |
| GET | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Fin Admin / Admin | Get transaction |
| PUT | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Fin Admin | Update transaction |
| DELETE | `/funding-accounts/{account_id}/transactions/{transaction_id}` | Fin Admin | Delete transaction |
| POST | `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice` | Fin Admin | Upload invoice |
| GET | `/funding-accounts/{account_id}/transactions/{transaction_id}/invoice` | Fin Admin / Admin | Download invoice |
| GET | `/statistics/funding` | Fin Admin / Admin | Funding statistics |
| GET | `/statistics/funding/{account_id}` | Fin Admin / Admin | Account statistics |
| GET | `/metrics/quality` | System Admin | Quality metrics |
| GET | `/metrics/quality/{activity_id}` | System Admin | Activity quality metrics |
| GET | `/alerts` | System Admin | List alerts |
| GET | `/alerts/{alert_id}` | System Admin | Get alert |
| PATCH | `/alerts/{alert_id}/acknowledge` | System Admin | Acknowledge alert |
| GET | `/audit-logs` | System Admin | List audit logs |
| GET | `/audit-logs/{log_id}` | System Admin | Get audit log |
| POST | `/data-collection/batches` | System Admin | Create batch |
| GET | `/data-collection/batches` | System Admin | List batches |
| GET | `/data-collection/batches/{batch_id}` | System Admin | Get batch |
| PATCH | `/data-collection/batches/{batch_id}/execute` | System Admin | Execute batch |
| GET | `/data-collection/batches/{batch_id}/results` | System Admin | Batch results |
| POST | `/similarity/check` | System Admin | Reserved (disabled) |
| POST | `/reports/reconciliation` | Fin Admin / Admin | Reconciliation report |
| POST | `/reports/audit` | System Admin | Audit report |
| POST | `/reports/compliance` | System Admin | Compliance report |
| GET | `/reports` | Admin / Fin Admin | List reports |
| GET | `/reports/{report_id}/download` | Admin / Fin Admin | Download report |
| GET | `/backups` | System Admin | List backups |
| POST | `/backups` | System Admin | Manual backup |
| POST | `/backups/{backup_id}/restore` | System Admin | Restore from backup |
