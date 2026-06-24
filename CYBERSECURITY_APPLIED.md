# Cybersecurity Applied to This Project

This document lists the cybersecurity controls currently applied in the IoT PF1 project, based on the backend, frontend, scan bridge, and security planning files.

## Applied Security Controls

### 1. Supabase Authentication

- The project uses Supabase Auth for user login and signup.
- Backend protected routes verify Supabase access tokens from the `Authorization: Bearer <token>` header.
- The backend derives the authenticated `user_id` from the verified token instead of trusting request body or query parameters.

Relevant files:

- `backend/deps/auth.py`
- `backend/routers/auth/login.py`
- `backend/routers/auth/signup.py`
- `backend/routers/auth/logout.py`

### 2. Protected Backend Routes

- Card management routes require authentication.
- Dashboard analytics and history routes require authentication.
- Card registration mode requires authentication before a user can start the registration flow.

Relevant files:

- `backend/routers/users.py`
- `backend/routers/dashboard.py`
- `backend/routers/scan_card.py`

### 3. User-Owned Access Control

- RFID cards are scoped to the authenticated user.
- Users can only view cards where `rfid_cards.user_id` matches their authenticated user ID.
- Users can only revoke or delete cards that belong to them.
- New cards are inserted with the authenticated user's `user_id`.

Relevant file:

- `backend/routers/users.py`

### 4. Password Handling

- Passwords are handled by Supabase Auth.
- Plaintext passwords are not inserted into the application's `users` table.
- Backend signup and login models enforce a minimum password length of 8 characters.

Relevant files:

- `backend/routers/auth/login.py`
- `backend/routers/auth/signup.py`

### 5. Login and Signup Rate Limiting

- The backend uses SlowAPI for rate limiting.
- Login requests are limited to reduce brute-force attempts.
- Signup requests are limited to reduce abuse and spam account creation.
- Rate limiting is attached globally to the FastAPI app.

Relevant files:

- `backend/deps/rate_limit.py`
- `backend/main.py`
- `backend/routers/auth/login.py`
- `backend/routers/auth/signup.py`

### 6. CORS Restriction

- CORS is configured with explicit local frontend origins.
- The backend does not allow every origin by default.

Relevant file:

- `backend/main.py`

### 7. Frontend Session Guard

- The Vue router blocks protected pages when no valid session exists.
- Expired sessions are cleared from local storage.
- Authenticated users are redirected away from login/signup pages.

Relevant files:

- `frontend/src/router/index.js`
- `frontend/src/utils/auth.js`

### 8. Bearer Token API Requests

- Frontend service modules attach the Supabase access token to protected backend requests.
- User card APIs and dashboard APIs send the token through the `Authorization` header.

Relevant files:

- `frontend/src/services/user.js`
- `frontend/src/services/dashboard.js`
- `frontend/src/utils/auth.js`

### 9. Logout and Session Cleanup

- Backend logout calls Supabase `sign_out()`.
- Frontend logout clears local session data even if the network request fails.

Relevant files:

- `backend/routers/auth/logout.py`
- `frontend/src/utils/auth.js`

### 10. RFID Card Validation Rules

- The scan validation route checks whether a card exists.
- Revoked cards are rejected.
- Active cards are granted.
- Unknown cards are rejected.
- When a `user_id` is supplied, card lookup is scoped to that owner.

Relevant file:

- `backend/routers/scan_card.py`

### 11. Access Logging

- Scan attempts are logged to the `access_logs` table.
- Logs include card ID, card name, user ID, status, timestamp, and optional rejection reason.
- A separate access-log route filters logs by authenticated `user_id`.

Relevant files:

- `backend/routers/scan_card.py`
- `backend/routers/access-logs.py`

### 12. Security and Operational Logging

- Failed login and signup attempts are logged with IP context.
- Scan validation results are logged.
- Supabase/database errors are logged server-side.
- WebSocket connect and disconnect events are logged.
- The scan bridge logs serial, API, and RFID scan activity.

Relevant files:

- `backend/routers/auth/login.py`
- `backend/routers/auth/signup.py`
- `backend/routers/scan_card.py`
- `backend/websocket/manager.py`
- `backend/receive_script/scan.py`

### 13. Environment-Based Secret Loading

- Supabase configuration is loaded from environment variables.
- The backend fails startup if required Supabase values are missing.
- The Supabase secret key is used in backend code, not frontend service modules.

Relevant file:

- `backend/supabase_client/supabase.py`

## Partially Applied or Still Needs Work

These items are documented in the security implementation plan or partially present in the codebase, but are not fully implemented yet.

### 1. Scan Bridge Device Authentication

- The scan bridge endpoints are currently callable without trusted-device authentication.
- HMAC signing with `X-Device-Id`, `X-Timestamp`, `X-Nonce`, and `X-Signature` is still planned.

Affected endpoints:

- `POST /scan-card/validate`
- `GET /scan-card/register-status`
- `POST /scan-card/forward-registration`
- `POST /scan-card/log`

### 2. WebSocket Authentication and User Scoping

- WebSocket connections are currently accepted without a token.
- WebSocket events are broadcast to all connected clients.
- Events are not yet scoped to the authenticated card owner or registration requester.

Relevant files:

- `backend/routers/scan_card.py`
- `backend/websocket/manager.py`
- `backend/websocket/events.py`
- `frontend/src/composables/useWebSocket.js`

### 3. Dashboard Log Filtering Gap

- Some dashboard queries include `card_id.is.null`.
- This can expose unknown-card logs broadly unless those logs are also scoped by `user_id`.
- The safer model is to query `access_logs.user_id == authenticated user_id`.

Relevant file:

- `backend/routers/dashboard.py`

### 4. Error Response Sanitization

- Some API errors still return raw exception details to clients.
- Safer responses should use generic client messages and keep details in server logs only.

Examples to improve:

- `Database error: {exc}`
- `Token verification failed: {exc}`
- `Failed to log in: {exc}`

### 5. Production HTTPS and WSS

- Frontend API and WebSocket URLs are still hardcoded to local development values.
- Production should use environment variables with HTTPS and WSS.
- Security headers such as HSTS, CSP, `X-Content-Type-Options`, and `Referrer-Policy` are still planned.

Relevant files:

- `frontend/src/utils/auth.js`
- `frontend/src/services/user.js`
- `frontend/src/services/dashboard.js`
- `frontend/src/composables/useWebSocket.js`
- `backend/receive_script/scan.py`

### 6. Stronger Input Validation

- Some fields still need stricter validation.
- Recommended constraints include card hash format, card role enum, status enum, card name length limits, and bounded dashboard history limits.

Relevant files:

- `backend/routers/users.py`
- `backend/routers/scan_card.py`
- `backend/routers/dashboard.py`

### 7. Step-Up Authentication

- Sensitive actions such as registering, revoking, and deleting cards do not yet require password reconfirmation, OTP, MFA, or a local action PIN.

### 8. Supabase Row-Level Security Review

- The backend enforces user ownership in application code.
- Supabase Row-Level Security policies should also be reviewed or added for defense in depth.

Recommended tables:

- `users`
- `rfid_cards`
- `access_logs`

### 9. Security Regression Tests

- Security-specific tests are not yet present.
- Tests should cover unauthenticated access, cross-user card access, revoked cards, unsigned scan requests, invalid HMAC signatures, and unauthenticated WebSocket connections.

## Summary

The project currently applies authentication, route protection, user-owned RFID card access control, login/signup throttling, CORS restrictions, frontend route guards, access logging, and environment-based secret loading.

The most important remaining security work is to authenticate the scan bridge, scope WebSocket events per user, fix dashboard log filtering, sanitize error responses, and prepare HTTPS/WSS production configuration.
