# CivicConnect M3 Interface Agreement

**Owner:** Don (backend contract)
**Status:** Backend routes implemented. Templates implemented against this exact contract
(2026-10-16) and verified through the Flask test client against the backend (`tests/test_m3_backend_routes.py`
- 16/16 passing, including the full login â†’ detail â†’ accept â†’ notification path through the
actual Flask app, not just each side in isolation). Still awaiting team review and Masego's
independent journey verification.
**Purpose:** Shared route, data, form, validation, and traceability contract for Emile (templates) and Masego (verification).
## Route Contract

| Capability | Method and URL | Allowed roles | Template and data supplied | Form/query fields and CSRF | Validation, error behavior, service | Traceability |
|---|---|---|---|---|---|---|
| Login | GET/POST `/login` | Public | `login.html`: `error`, `csrf_token` | POST: `email`, `password`, `csrf_token`; CSRF required | Invalid credentials return the same message with HTTP 200; invalid CSRF returns 400. Bcrypt verification; a valid legacy Werkzeug hash is upgraded. | FR-002 / AC-002; NFR-003 / AC-N003; NFR-004 / AC-N004 |
| Logout | POST `/logout` | Any authenticated role | No response template; redirects to login | `csrf_token`; required | Invalid CSRF returns 400; otherwise clear session and redirect. No service method. | FR-002 / AC-002; FR-003 / AC-003 |
| Request submission form | GET `/requests/new` | Requester | Existing `new_request.html`: `categories` as `(id, name)` rows, `error`, `values`, `csrf_token` | No submission fields on GET | Other roles receive 403. Active categories loaded by the route. | FR-005 / AC-005; FR-006 / AC-006 |
| Submit request | POST `/requests` | Requester | Success redirects to confirmation; validation failure re-renders `new_request.html` with `categories`, `error`, `values`, `csrf_token` | `title`, `description`, `category_id`, `location`, `csrf_token`; CSRF required | Invalid CSRF: 400; wrong role: 403; service `ValueError`: 400 with entered values retained. Calls `RequestService.create_request`. | FR-005 / AC-005; FR-006 / AC-006; NFR-014 / AC-N014 |
| Submission confirmation | GET `/requests/<request_id>/submitted` | Owning Requester | Existing `confirmation.html`: `request_id` | None | Missing or non-owned request: 404. Direct ownership lookup. | FR-005 / AC-005; FR-008 / AC-008 |
| Requester list and status filter | GET `/requests[?status=<status>]` | Requester | `requester_requests.html`: `requests` (each: `reference`, `title`, `category`, `submitted_at`, `status`, `last_status_changed_at`), `statuses`, `selected_status` | Optional query `status`; no CSRF | Invalid status: 400. Role and ownership enforced by `RequestService.list_requester_requests`; SQL values are parameterized. | FR-007 / AC-007; FR-008 / AC-008; FR-012 / AC-012; NFR-001 / AC-N001 |
| Request detail | GET `/requests/<request_id>` | Owning Requester; Staff when unassigned or assigned to them; Manager; Administrator | `request_detail.html`: `request` dict (`reference`, `assignee_id`, `category_id`, `title`, `description`, `location`, `status`, `version`, `submitted_at`, `updated_at`, `accepted_at`, `last_status_changed_at`, `category`, optional `assignee_email`, conditionally supplied `requester_email`, `history`); plus `csrf_token`, `can_accept` | No fields on GET; acceptance form uses the POST contract below | Missing, non-owned, or assigned-to-other Staff request: 404. Disallowed role: 403. Service `RequestService.get_request_detail` enforces record access. `requester_email` is withheld from Requesters and unassigned Staff. | FR-007 / AC-007; FR-013 / AC-013; FR-025 / AC-025; NFR-004 / AC-N004; NFR-006 / AC-N006; NFR-012 / AC-N012 |
| Staff queue and status filter | GET `/staff/queue[?status=<status>]` | Staff | `staff_queue.html`: `requests` (each: `reference`, `title`, `category`, `submitted_at`, `status`, `assignee_id`, `last_status_changed_at`), `statuses`, `selected_status` | Optional query `status`; no CSRF | Invalid status: 400; other roles: 403. `RequestService.list_staff_queue` returns unassigned and this Staff user's requests only; SQL values are parameterized. | FR-011 / AC-011; FR-012 / AC-012; NFR-001 / AC-N001; NFR-004 / AC-N004 |
| Staff self-acceptance | POST `/staff/requests/<request_id>/accept` | Staff | Success redirects to `/requests/<request_id>`; conflict response otherwise | `expected_version`, `csrf_token`; CSRF required | Invalid CSRF: 400; other role: 403; malformed/negative version: 400; stale version, missing request, or invalid transition: 409. Calls `RequestService.accept_request`; audit, state, and outbox writes are transactional. | FR-014 / AC-014; FR-015 / AC-015 (only New -> Accepted specified); FR-009 / AC-009; FR-025 / AC-025; NFR-004 / AC-N004; NFR-006 / AC-N006 |
| Notifications | GET `/notifications` | Requester | `notifications.html`: `notifications` (each: `id`, `request_id`, `event_type`, `message`, `created_at`, `read_at`) | None | Other roles: 403. `RequestService.list_notifications` returns only the current Requester's notifications. | FR-009 / AC-009; NFR-012 / AC-N012 |
| Safe role landing | GET `/landing` | Manager, Administrator | `role_landing.html`: `role` | None | Other roles: 403. No redirect to Requester pages. Manager dashboard and Administrator operations remain deferred; this page must not imply those features exist. | FR-003 / AC-003; NFR-004 / AC-N004 |

## Shared Rules

- All application routes other than `/login` and static assets require an active session. Identity comes from the session, never a submitted user ID.
- Every state-changing form includes `csrf_token`; the backend validates it before acting.
- Service-layer checks remain authoritative even when the route also checks a role.
- Valid status values: `New`, `Accepted`, `In Progress`, `On Hold`, `Resolved`, `Closed`, `Rejected`. Unknown filters are rejected, not interpolated into SQL.
- History is the ordered audit log. Comments and resolution notes are absent from the current schema; do not fabricate those fields or claim FR-010/FR-016 detail is complete.
- `requester_email` is supplied only to Manager/Administrator and the Staff member assigned to that request.
- `/landing` is deliberately informational and non-operational for Manager/Administrator until their scoped features are implemented.

## Template Handoff

All templates listed above are present in this integration candidate. The shared context provides `current_user` and a session CSRF token on authenticated pages, including list and landing pages. Contract changes still require review by Don and Masego.

## Verification Handoff

Masego owns verification tests and RTM updates. Add coverage for role boundaries, requester ownership, Staff queue scoping, allowed/invalid filters, CSRF rejection, optimistic-concurrency conflict, audit/outbox atomicity, and notification delivery. Link test IDs to existing TR/AC identifiers; do not create or renumber requirement IDs here.
