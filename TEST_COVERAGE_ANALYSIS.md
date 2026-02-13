# Test Coverage Analysis

## Current State

This codebase has **no formal testing infrastructure**. There is no test framework (pytest), no
test runner configuration, no coverage tooling, and no CI/CD pipeline. The only "tests" are three
ad-hoc Python scripts at the repository root that require a running database or server:

| Script | What it does |
|--------|-------------|
| `test_policy_logic.py` | Directly manipulates SQLAlchemy sessions to verify approval policy logic |
| `test_voice_assistant.py` | Makes HTTP requests to a running server to test the chat endpoint |
| `demo_approval_system.py` | Demonstrates the approval workflow by hitting the DB directly |

These scripts are not runnable by `pytest`, have no assertions using a test framework, and depend
on external state (a live database or running server). They provide zero repeatable, automated
coverage.

---

## Source Module Inventory

### Backend (`app/`)

| Module | File | Lines | Covered by existing scripts? |
|--------|------|-------|------------------------------|
| **Models** | `models/core.py` (User, ApprovalMixin, ApprovalPolicy, enums) | 125 | Partially (approval mixin only) |
| **Models** | `models/masters.py` (Partner, PartnerType) | 30 | Partially (creation only) |
| **API** | `api/auth.py` (JWT, login, role checks) | 207 | No |
| **API** | `api/partners.py` (CRUD + approval endpoint) | 268 | No |
| **API** | `api/chat.py` (voice assistant endpoint) | 161 | Partially (manual HTTP) |
| **Services** | `services/approval_service.py` (approval engine) | 120 | Partially (happy path only) |
| **Services** | `services/chat_service.py` (NLP intent detection) | 307 | No |
| **Database** | `database.py` (engine, session, get_db) | 42 | No |
| **App** | `main.py` (FastAPI app, startup, health) | 114 | No |

### Frontend (`frontend/src/`)

| Module | File |
|--------|------|
| Pages | `Login.jsx`, `Dashboard.jsx`, `Partners.jsx` |
| Layout | `MainLayout.jsx` |
| Components | `ProtectedRoute.jsx` |
| Services | `api.js` |
| Config | `App.jsx`, `theme.js`, `main.jsx` |

**Frontend test coverage: 0%.** No test framework (Vitest/Jest) is installed.

---

## Coverage Gap Analysis by Module

### 1. `services/approval_service.py` — HIGH PRIORITY

The approval engine is the core business logic of this application. It currently has the largest
coverage gap relative to its importance.

**What needs testing:**

- `check_approval_required()` — when no policy exists (auto-approve path)
- `check_approval_required()` — when an active policy exists and user role is sufficient
- `check_approval_required()` — when an active policy exists and user role is insufficient
- `check_approval_required()` — when a policy exists but `is_active=False`
- `determine_workflow_stage()` — returns `APPROVED` vs `PENDING_APPROVAL` correctly
- `_user_has_required_role()` — every combination in the role hierarchy (ADMIN > MANAGER > ACCOUNTANT > SALESMAN)
- `_user_has_required_role()` — edge case: unknown role (defaults to level 0)
- `toggle_policy()` — activating, deactivating, and the case where the policy doesn't exist (returns `None`)
- `get_active_policies()` — with mixed active/inactive policies

### 2. `api/auth.py` — HIGH PRIORITY

Authentication is security-critical and has zero automated test coverage.

**What needs testing:**

- `POST /api/v1/auth/token` — successful login returns valid JWT with correct claims
- `POST /api/v1/auth/token` — wrong password returns 401
- `POST /api/v1/auth/token` — nonexistent user returns 401
- `POST /api/v1/auth/token` — inactive user returns 401
- `GET /api/v1/auth/me` — returns correct user data for valid token
- `GET /api/v1/auth/me` — returns 401 for expired token
- `GET /api/v1/auth/me` — returns 401 for malformed token
- `create_access_token()` — token contains correct `sub`, `username`, `role`, `exp` claims
- `verify_token()` — rejects tokens with missing claims (`sub`, `username`, `role`)
- `verify_token()` — rejects expired tokens
- `authenticate_user()` — correct password, wrong password, missing user, inactive user
- `require_role()` — each role level allowed/denied based on hierarchy
- `require_role()` — ADMIN can access MANAGER-restricted endpoints
- `require_role()` — SALESMAN cannot access MANAGER-restricted endpoints

### 3. `api/partners.py` — HIGH PRIORITY

The partner CRUD + approval workflow is the primary user-facing feature.

**What needs testing:**

- `POST /api/v1/partners/` — creates partner with `PENDING_APPROVAL` when approval policy is active and user is SALESMAN
- `POST /api/v1/partners/` — creates partner with `APPROVED` when user is ADMIN (auto-approve)
- `POST /api/v1/partners/` — rejects duplicate GST number with 400
- `POST /api/v1/partners/` — handles `None` credit_limit (defaults to 0.00)
- `GET /api/v1/partners/` — returns all partners, respects pagination (`skip`, `limit`)
- `GET /api/v1/partners/` — filters by `workflow_stage` query param
- `GET /api/v1/partners/{id}` — returns partner by ID
- `GET /api/v1/partners/{id}` — returns 404 for nonexistent ID
- `PUT /api/v1/partners/{id}/approve` — approve action sets `APPROVED` stage and `approved_by_id`
- `PUT /api/v1/partners/{id}/approve` — reject action requires a reason
- `PUT /api/v1/partners/{id}/approve` — reject without reason returns 400
- `PUT /api/v1/partners/{id}/approve` — cannot approve an already-approved partner (400)
- `PUT /api/v1/partners/{id}/approve` — SALESMAN cannot access this endpoint (403)
- `PUT /api/v1/partners/{id}/approve` — invalid action string returns 400
- `GET /api/v1/partners/pending/count` — returns correct count, MANAGER+ only

### 4. `services/chat_service.py` — MEDIUM PRIORITY

The NLP service has complex branching logic that is well-suited for unit tests.

**What needs testing:**

- `normalize_message()` — lowercasing, whitespace collapsing, voice artifact removal ("um", "uh")
- `normalize_message()` — empty string, `None`, whitespace-only input
- `detect_intent()` — each intent pattern: `approvals`, `list_partners`, `help`, `unknown`
- `detect_intent()` — ambiguous messages that match multiple patterns (first match wins)
- `handle_approvals_intent()` — SALESMAN sees limited results (limit 1)
- `handle_approvals_intent()` — MANAGER/ADMIN sees all pending
- `handle_approvals_intent()` — zero pending approvals message
- `handle_approvals_intent()` — database error path
- `handle_list_partners_intent()` — SALESMAN sees approved only (limit 3)
- `handle_list_partners_intent()` — other roles see last 5 created
- `handle_help_intent()` — returns role-specific commands for each role
- `process_message()` — empty input, whitespace-only input, fully normalized-to-empty input
- `process_message()` — routing to correct handler per detected intent

### 5. `models/core.py` — MEDIUM PRIORITY

Model logic (password hashing, approval mixin methods) should be unit tested.

**What needs testing:**

- `User.set_password()` / `User.verify_password()` — round-trip correctness
- `User.set_password()` — passwords longer than 72 bytes are truncated
- `User.verify_password()` — wrong password returns `False`
- `ApprovalMixin.approve()` — sets `APPROVED`, `approved_by_id`, clears `rejection_reason`
- `ApprovalMixin.reject()` — sets `REJECTED`, stores reason and rejector
- `ApprovalMixin.submit_for_approval()` — transitions from `DRAFT` to `PENDING_APPROVAL`

### 6. `api/chat.py` — MEDIUM PRIORITY

**What needs testing:**

- `POST /api/v1/chat/` — successful message processing returns structured response
- `POST /api/v1/chat/` — empty message rejected by Pydantic validation (min_length=1)
- `POST /api/v1/chat/` — message over 500 chars rejected (max_length=500)
- `POST /api/v1/chat/` — unauthenticated request returns 401
- `GET /api/v1/chat/help` — returns role-specific help
- `GET /api/v1/chat/intents` — returns intent catalog

### 7. `main.py` — LOW PRIORITY

**What needs testing:**

- `GET /` — returns system info
- `GET /health` — returns health status with DB connectivity
- Startup event creates tables without error
- CORS headers are present on responses

### 8. Frontend — LOW PRIORITY (but 0% coverage)

**What needs testing (when a frontend test framework is added):**

- `api.js` — token storage/retrieval, request interceptor attaches auth header, 401 response interceptor clears token
- `ProtectedRoute.jsx` — redirects to login when no token, renders children when authenticated
- `Login.jsx` — form submission, error display, demo user buttons
- `Dashboard.jsx` — data fetching, stat card rendering
- `Partners.jsx` — CRUD operations, approval/rejection dialogs, role-based UI

---

## Recommended Infrastructure Setup

Before writing any tests, the following infrastructure should be established:

### Backend

1. **Add test dependencies to `requirements.txt`:**
   - `pytest` — test runner
   - `pytest-asyncio` — async test support for FastAPI
   - `httpx` — async test client for FastAPI (used with `TestClient`)
   - `pytest-cov` — coverage reporting
   - `factory-boy` — test data factories (optional but recommended)

2. **Create `conftest.py` with:**
   - An in-memory SQLite test database engine
   - A `db_session` fixture that creates tables, yields a session, and rolls back after each test
   - A `client` fixture providing a FastAPI `TestClient` with dependency overrides for `get_db`
   - User factory fixtures for each role (admin, manager, accountant, salesman)
   - A helper to generate valid JWT tokens for any test user

3. **Create a `tests/` directory structure:**
   ```
   tests/
   ├── conftest.py
   ├── test_models/
   │   ├── test_user.py
   │   └── test_partner.py
   ├── test_services/
   │   ├── test_approval_service.py
   │   └── test_chat_service.py
   └── test_api/
       ├── test_auth.py
       ├── test_partners.py
       └── test_chat.py
   ```

4. **Add a `pytest.ini` or `[tool.pytest.ini_options]` in `pyproject.toml`:**
   - Configure test paths, coverage targets, and async mode

### Frontend

1. **Install Vitest + React Testing Library** (Vitest integrates natively with Vite)
2. **Add test scripts to `package.json`**: `"test": "vitest"`, `"test:coverage": "vitest --coverage"`

---

## Prioritized Implementation Order

| Priority | Area | Type | Estimated Tests | Impact |
|----------|------|------|----------------|--------|
| **P0** | Test infrastructure (conftest, fixtures) | Setup | — | Enables everything else |
| **P1** | `services/approval_service.py` | Unit | ~12 | Core business logic |
| **P1** | `api/auth.py` | Unit + Integration | ~14 | Security critical |
| **P1** | `api/partners.py` | Integration | ~15 | Primary feature |
| **P2** | `models/core.py` (User, ApprovalMixin) | Unit | ~8 | Data integrity |
| **P2** | `services/chat_service.py` | Unit | ~15 | Complex branching |
| **P2** | `api/chat.py` | Integration | ~6 | Secondary feature |
| **P3** | `main.py` (root, health) | Integration | ~4 | Smoke tests |
| **P3** | Frontend (api.js, components) | Unit | ~20 | UI correctness |

**Total estimated: ~94 tests to achieve reasonable coverage across the backend.**

---

## Key Risks from Missing Tests

1. **Approval logic regressions**: The approval engine has no guard against regressions. A change to `_user_has_required_role()` could silently allow unauthorized approvals.

2. **Authentication bypass**: `verify_token()` and `require_role()` are untested. A refactoring error could expose all endpoints to unauthenticated users.

3. **Data integrity**: No tests verify that duplicate GST numbers are rejected, that rejection reasons are required, or that workflow stage transitions are valid.

4. **NLP intent misrouting**: The regex-based intent detection in `chat_service.py` could silently break with pattern changes, routing users to wrong handlers.

5. **Role hierarchy inversion**: The role hierarchy is duplicated in `approval_service.py:82` and `auth.py:139`. If these diverge, the system would have inconsistent access control.
