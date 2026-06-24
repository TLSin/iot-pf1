# Cybersecurity Implementation Plan

## 1. Security Model

This project follows a user-as-owner access-control model.

Each signed-up account owns and administers only its own RFID cards. A user can register, view, revoke, and remove only the cards associated with their authenticated `user_id`. There is no separate global administrator role in the current scope.

The implementation plan below strengthens that model while preserving the existing architecture:

- Vue frontend for login, dashboard, card management, and access logs.
- FastAPI backend for authentication, card APIs, dashboard APIs, scan validation, and WebSocket events.
- Supabase Auth for user authentication.
- Supabase Database for users, RFID cards, and access logs.
- `scan.py` serial bridge between the Arduino/RFID reader and FastAPI.

## 2. Implementation Priorities

| Priority | Enhancement | Main Risk Addressed |
|---|---|---|
| High | Add trusted-device authentication for scan bridge endpoints | Spoofed card scans, fake registrations, forged logs |
| High | Scope WebSocket events to authenticated users | Cross-user event leakage and card hash exposure |
| High | Fix access log ownership and filtering | Users seeing unrelated scan logs; weak accountability |
| High | Enforce production HTTPS/WSS configuration | Token, card hash, and API data interception |
| Medium | Add step-up authentication for sensitive card actions | Damage from compromised user sessions |
| Medium | Harden input validation | Malformed data, abuse, accidental database issues |
| Medium | Add rate limiting and abuse detection | Brute force login, scan spam, card hash guessing |
| Medium | Sanitize error responses | Information disclosure |
| Low | Repository and dependency hygiene | Supply-chain and release quality issues |
| Low | Security regression tests | Future security regressions |

## 3. Phase 1: Protect IoT Scan Bridge Endpoints

### Purpose

The scan endpoints are currently designed for `scan.py`, but they do not authenticate the device. Any client that can reach the backend could call scan validation, registration status, forward-registration, or manual log creation endpoints.

### Affected Backend Files

- `backend/routers/scan_card.py`
- `backend/receive_script/scan.py`
- `backend/.env`

### Implementation Tasks

1. Add device credentials to the backend environment:

   ```env
   SCAN_DEVICE_ID=reader-01
   SCAN_DEVICE_SECRET=<random-long-secret>
   ```

2. Add the same values to the environment used by `scan.py`.

3. Create a FastAPI dependency, for example `get_trusted_scan_device`, that validates:

   - `X-Device-Id`
   - `X-Timestamp`
   - `X-Nonce`
   - `X-Signature`

4. Generate `X-Signature` in `scan.py` using HMAC-SHA256:

   ```text
   HMAC(secret, method + path + timestamp + nonce + request_body)
   ```

5. Reject requests when:

   - device ID is unknown
   - signature is invalid
   - timestamp is too old
   - nonce has already been used

6. Apply the dependency to:

   - `POST /scan-card/validate`
   - `GET /scan-card/register-status`
   - `POST /scan-card/forward-registration`
   - `POST /scan-card/log`

### Acceptance Criteria

- Requests from `scan.py` succeed when signed correctly.
- Unsigned requests receive `401 Unauthorized`.
- Requests with modified body/signature receive `401 Unauthorized`.
- Replay of the same nonce is rejected.
- Normal user card management APIs still use Supabase bearer auth.

## 4. Phase 2: Scope WebSocket Events to Authenticated Users

### Purpose

The current WebSocket endpoint accepts any connection and broadcasts scan events to every connected dashboard. Under the user-as-owner model, events should only go to the owner of the related card or to the user who started registration.

### Affected Files

- `backend/routers/scan_card.py`
- `backend/websocket/manager.py`
- `backend/websocket/events.py`
- `frontend/src/composables/useWebSocket.js`
- `frontend/src/views/User View/UserView.vue`
- `frontend/src/views/Home View/HomeView.vue`
- `frontend/src/views/Access Log View/AccessLogView.vue`

### Implementation Tasks

1. Pass the Supabase access token when opening the WebSocket:

   ```text
   ws://localhost:8000/ws/scan?token=<access_token>
   ```

   In production, use:

   ```text
   wss://your-domain/ws/scan?token=<access_token>
   ```

2. Verify the token in the WebSocket route using the same Supabase verification logic as REST routes.

3. Store active WebSocket connections by `user_id` instead of one global list.

4. Change broadcast helpers so they can send to:

   - a specific `user_id`
   - the user who started registration
   - optionally all users only for non-sensitive system-wide events

5. In `validate_card`, when a registered card is found, broadcast the scan result only to `card.user_id`.

6. In registration flow, keep `triggered_by_user_id` until the card hash is forwarded, then send `registration_card_detected` only to that user.

7. Avoid broadcasting raw card hashes globally.

### Acceptance Criteria

- Unauthenticated WebSocket connections are rejected.
- User A does not receive scan or registration events for User B.
- Registration modal opens only for the user who requested registration.
- Existing dashboard live updates still work for the correct user.

## 5. Phase 3: Fix Access Log Ownership and Audit Fields

### Purpose

Access logs should be attributable to the card owner and queryable only by that owner. The current insert helper accepts `user_id` but does not insert it into `access_logs`.

### Affected Files

- `backend/routers/scan_card.py`
- `backend/routers/dashboard.py`
- Supabase `access_logs` table

### Database Changes

Add or confirm these columns on `access_logs`:

| Column | Purpose |
|---|---|
| `log_id` | Unique log identifier |
| `user_id` | Owner of the card or active registration context |
| `card_id` | Matched RFID card, nullable for unknown cards |
| `card_name` | Snapshot of card holder name |
| `status` | `granted` or `rejected` |
| `reason` | Rejection or event reason |
| `device_id` | Trusted scan reader that sent the event |
| `created_at` | Timestamp |

### Implementation Tasks

1. Update `_insert_access_log()` to insert `user_id`, `reason`, and `device_id`.

2. When a card is found, set `user_id` from the card row.

3. For unknown card scans, either:

   - do not show them in user dashboards, or
   - assign them to a known active registration user/device context.

4. Update `/dashboard/analytics` and `/dashboard/history` to query logs using:

   ```text
   access_logs.user_id == authenticated user_id
   ```

5. Remove broad `card_id.is.null` queries from user dashboards unless they are intentionally scoped by `user_id`.

### Acceptance Criteria

- User A cannot retrieve User B access logs.
- Unknown card scans are not globally visible to all users.
- Every access log has enough context for accountability.
- Dashboard counts match the authenticated user's own card/log data.

## 6. Phase 4: Production HTTPS and Configuration Cleanup

### Purpose

The current frontend and scan bridge use hardcoded local HTTP and WebSocket URLs. This is acceptable for development but not for production.

### Affected Files

- `frontend/src/utils/auth.js`
- `frontend/src/services/user.js`
- `frontend/src/services/dashboard.js`
- `frontend/src/composables/useWebSocket.js`
- `backend/receive_script/scan.py`
- frontend `.env`

### Implementation Tasks

1. Move API URLs into environment variables:

   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000/ws/scan
   ```

2. Use production values when deployed:

   ```env
   VITE_API_BASE_URL=https://your-domain
   VITE_WS_URL=wss://your-domain/ws/scan
   ```

3. Keep `FASTAPI_BASE_URL` in `scan.py` environment-based.

4. Configure TLS using a reverse proxy such as Nginx, Caddy, or a platform-managed HTTPS service.

5. Add security headers at the reverse proxy or FastAPI layer:

   - `Strict-Transport-Security`
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy`
   - `Content-Security-Policy`

### Acceptance Criteria

- No frontend source file hardcodes `http://localhost:8000`.
- Production uses HTTPS and WSS.
- Browser devtools show secure WebSocket and API connections.
- Local development remains easy through `.env` values.

## 7. Phase 5: Step-Up Authentication for Sensitive Actions

### Purpose

The current model accepts that each user administers their own cards. To reduce damage from account compromise, sensitive card actions can require a second confirmation step.

### Sensitive Actions

- Register new RFID card
- Revoke card
- Delete card
- Change account email or password, if added later

### Practical Options

| Option | Description | Complexity |
|---|---|---|
| Password re-confirmation | Ask user to re-enter password before sensitive action | Medium |
| Email OTP | Send one-time code before allowing card registration/deletion | Medium |
| Supabase MFA | Use Supabase-supported MFA if enabled | Medium to High |
| Local PIN | User configures a short action PIN | Low to Medium, but weaker |

### Recommended First Step

Start with password re-confirmation or email OTP for registering and deleting cards.

### Acceptance Criteria

- A logged-in user cannot register/delete a card without completing step-up verification.
- Step-up verification expires after a short period, such as 5 minutes.
- Failed step-up attempts are rate-limited and logged.

## 8. Phase 6: Input Validation Hardening

### Purpose

Stronger validation reduces malformed records, abuse, and unexpected database behavior.

### Implementation Tasks

1. Add constraints to Pydantic models:

   - `card_hash`: fixed length or allowed pattern, for example hexadecimal only
   - `card_name`: minimum and maximum length
   - `card_role`: enum or allowed list
   - `status`: enum of `granted` and `rejected`
   - `limit`: bounded integer, for example 1 to 100

2. Normalize card status values:

   - Use `active`
   - Use `revoked`
   - Avoid mixing `revoke` and `revoked`

3. Validate frontend forms before submission for better UX, but keep backend validation authoritative.

### Acceptance Criteria

- Invalid card hashes are rejected before database lookup.
- Excessively long names/roles are rejected.
- Dashboard history limits cannot request unbounded results accidentally.
- Revoked-card status is consistent across backend and frontend.

## 9. Phase 7: Rate Limiting and Abuse Detection

### Purpose

Rate limiting protects the app from brute force login, scan spam, and repeated rejected-card attempts.

### Implementation Tasks

1. Add API rate limiting middleware.

2. Suggested limits:

   | Endpoint Type | Suggested Limit |
   |---|---|
   | Login | 5 attempts per minute per IP/email |
   | Signup | 3 attempts per hour per IP |
   | Scan validation | Device-specific limit based on expected scan volume |
   | Registration mode | 5 attempts per minute per user |
   | Card delete/revoke | 10 attempts per minute per user |

3. Log suspicious patterns:

   - many rejected scans
   - repeated invalid device signatures
   - repeated failed login attempts
   - frequent registration attempts

### Acceptance Criteria

- Excessive login attempts are throttled.
- Excessive scan requests from an invalid source are blocked.
- Logs identify suspicious activity without exposing secrets.

## 10. Phase 8: Error Response Sanitization

### Purpose

Raw exception messages can reveal database structure, authentication internals, or infrastructure details.

### Implementation Tasks

1. Replace client-facing messages such as:

   ```text
   Database error: {exc}
   Token verification failed: {exc}
   Failed to log in: {exc}
   ```

   with generic messages:

   ```text
   Database operation failed.
   Invalid or expired token.
   Authentication failed.
   ```

2. Keep detailed exception information in server logs only.

3. Add request IDs to correlate client errors with backend logs.

### Acceptance Criteria

- API clients receive safe, generic error messages.
- Backend logs retain enough detail for debugging.
- No secrets, SQL details, or token internals are returned to the frontend.

## 11. Phase 9: Supabase Row-Level Security Review

### Purpose

The backend uses Supabase with a secret key. The application code enforces user ownership, but database-level policies should also support the same security model where practical.

### Implementation Tasks

1. Confirm Row Level Security is enabled on:

   - `users`
   - `rfid_cards`
   - `access_logs`

2. Add policies matching the user-as-owner model:

   - users can select/update only their own profile
   - users can select cards where `rfid_cards.user_id = auth.uid()`
   - users can select logs where `access_logs.user_id = auth.uid()`

3. Keep service-role operations restricted to backend-only workflows.

4. Never expose the Supabase secret/service key to the frontend.

### Acceptance Criteria

- Supabase policies reflect the same ownership rules as FastAPI.
- Frontend uses only safe public configuration.
- Accidental direct database access does not bypass user ownership.

## 12. Phase 10: Repository Hygiene and Security Testing

### Repository Cleanup

1. Remove tracked Python cache files:

   ```text
   backend/**/__pycache__/*.pyc
   ```

2. Add or confirm ignore rules for:

   ```text
   __pycache__/
   *.pyc
   .env
   node_modules/
   dist/
   ```

3. Add `.env.example` files without secrets.

4. Add backend dependency tracking, such as:

   - `requirements.txt`
   - `pyproject.toml`
   - lock file, if using a package manager that supports one

### Security Tests

Add tests for:

- unauthenticated REST card APIs return `401`
- User A cannot access User B cards
- User A cannot access User B logs
- revoked cards are rejected
- unsigned scan bridge requests are rejected
- invalid HMAC signatures are rejected
- WebSocket connections without valid token are rejected
- registration event goes only to the requesting user

### Acceptance Criteria

- Security tests run locally.
- Cache files are no longer tracked.
- Environment examples document required variables safely.
- Dependency versions are reviewable.

## 13. Suggested Rollout Order

1. Fix access log `user_id` storage and dashboard filtering.
2. Add scan bridge device authentication.
3. Authenticate and scope WebSocket connections.
4. Move frontend/backend URLs into environment variables and prepare HTTPS/WSS.
5. Add validation constraints and safer error responses.
6. Add rate limiting.
7. Add step-up authentication for card registration/deletion.
8. Review Supabase RLS policies.
9. Clean repository artifacts and add security tests.

## 14. Expected Security Benefits

After implementation, the system will provide stronger:

- Confidentiality: users see only their own cards, logs, and scan events.
- Integrity: scan and registration events come only from trusted devices and authenticated users.
- Availability: rate limits reduce brute force attempts and scan spam.
- Accountability: access logs identify the user, card, device, status, and reason.
- Access control: ownership rules are enforced consistently in frontend flow, backend APIs, WebSocket events, and database policy.
- Resilience: compromised sessions can be limited through future step-up verification for sensitive card actions.

