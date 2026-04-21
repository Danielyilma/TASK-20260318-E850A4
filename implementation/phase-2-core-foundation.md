## Phase 2: Core Foundation

### Goals
- Implement the core database schema for `User` and `Activity` entities.
- Create and execute database migrations via Alembic.
- Build basic CRUD APIs, focusing initially on `Activities`.
- Setup global state management and API integration layout on the frontend.

### Backend Implementation
1. **Entity Models:**
   - Define the `User` SQLAlchemy model with all fields (`id`, `username`, `password_hash`, `role`, `id_number`, `contact_info`, `is_locked`, `failed_login_attempts`, timestamps).
   - Define the `Activity` SQLAlchemy model (`id`, `name`, `description`, `deadline`, `budget`, `is_active`, timestamps).
2. **Database Migrations:** Run Alembic to auto-generate migration scripts for `User` and `Activity` and apply them (`alembic upgrade head`).
3. **Pydantic Schemas:** Set up request/response schemas corresponding to the api-spec for `User` and `Activity` resources (e.g., `ActivityCreate`, `ActivityRead`).
4. **Repository Layer:** Create a base repository pattern or SQLAlchemy session management dependency (`get_db`).
5. **Activity Endpoints:** Implement endpoints defined in `api-spec.md`:
   - `POST /api/v1/activities`
   - `GET /api/v1/activities` (with pagination structure)
   - `GET /api/v1/activities/{activity_id}`
   - `PUT /api/v1/activities/{activity_id}`
   - `DELETE /api/v1/activities/{activity_id}`

### Frontend Implementation
1. **Global State:** Configure Pinia. Create an `activityStore` to fetch and store the list of available activities.
2. **API Service Base:** Implement explicit API functions in `src/services/activity.service.js` corresponding to the Activity backend endpoints.
3. **Basic UI Pages:**
   - Create an `ActivityList.vue` page showcasing a data table of activities.
   - Create an `ActivityDetail.vue` page to show individual activity information.
4. **Mocked Dev Setup:** Since Auth isn't fully implemented yet, bypass strict permission guards temporarily or supply a mock System Admin token for dev.

### Testing Plan
- **Tools:** Use `pytest` for backend, `vitest` for frontend.
- **Backend Tests:**
   - **Model Tests:** Write unit tests to check constraint compliance (e.g., missing name triggers DB error).
   - **API Tests:** Write `test_create_activity`, `test_get_activities`, `test_get_single_activity`, `test_update_activity`, and `test_delete_activity`. Confirm schema validation works (e.g., 400 Validation Error on negative budget).
- **Frontend Tests:**
   - Test `ActivityList.vue` renders correctly when mocked data is provided from the `activityStore`.

### Definition of Done
- `alembic upgrade head` runs perfectly on an empty DB creating the tables.
- `Activity` endpoints pass all API unit tests with 200/201 responses.
- Frontend successfully queries and displays `Activities` fetched from the backend.
