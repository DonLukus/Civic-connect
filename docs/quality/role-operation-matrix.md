# M3 role x operation authorisation matrix

Owner: Masego. Written against the integration candidate `m3/emile-release-verification`
(commit `f40c02d` at the time this was written), per `docs/quality/m3-verification-handoff.md`
point 2 and the release evidence summary's "Full role matrix" residual risk — representative
denials in existing tests do not prove every restricted operation for every role, and NFR-004
("100% of role-restricted operations reject unauthorised access") cannot honestly be claimed
without this.

**Every cell below is now backed by a passing automated test that hits the real HTTP route.**

**Correction (16 Oct 2026):** an earlier version of this document claimed every prior
role/ownership check ran at the `RequestService` layer only, never through the route. That
overclaimed it — `test_m3_backend_routes.py`'s `test_route_request_list_allows_requester_
blocks_staff`, `test_route_staff_queue_allows_staff_blocks_requester`,
`test_route_accept_rejects_bad_csrf_and_wrong_role` and `test_route_notifications_and_landing`
(TST-029/030/032/033) already hit real HTTP routes, not the service layer, for Requester-vs-Staff
blocking. What was actually missing, and is what this file closes:

1. `GET /requests/<id>` (request detail) role/ownership enforcement — `test_request_detail_
   owner_can_view_non_owner_cannot` and `test_request_detail_staff_visibility_follows_assignment`
   call `service.get_request_detail(...)` directly, never through the route. A route-wiring bug
   (wrong actor id, an exception not mapped to the right HTTP status) would not have been caught.
2. **Manager and Administrator had no authorisation coverage against any route before this** —
   neither "correctly blocked from" nor "correctly allowed into." The one exception was
   `GET /landing`, tested positively for Manager only, and for Administrator only inside
   `test_m3_logout.py` — a logout/session-mechanics test, not an authorisation test; it never
   asserted Administrator is blocked from anything, or allowed into `/landing` for authorisation
   reasons rather than as a side effect of a login/logout sequence.
3. Several routes had only one direction of their role check tested (e.g. `/landing`: Requester
   blocked and Manager allowed were tested; Staff-blocked and Administrator-allowed were not).

## The matrix

✅ = operation permitted and correctly returns the expected successful response.
🚫 = operation rejected (403, or 404 where revealing existence would itself leak information).
— = route is not role-gated this way for this role (see per-row notes).

| Operation (route) | Requester | Staff | Manager | Administrator |
|---|---|---|---|---|
| `GET /requests/new` (submission form) | ✅ | 🚫 403 | 🚫 403 | 🚫 403 |
| `POST /requests` (submit a request) | ✅ | 🚫 403 | 🚫 403 | 🚫 403 |
| `GET /requests/<id>/submitted` (confirmation) | ✅ own / 🚫 404 other Requester | 🚫 403 | 🚫 403 | 🚫 403 |
| `GET /requests` (own request list) | ✅ | 🚫 403 | 🚫 403 | 🚫 403 |
| `GET /notifications` | ✅ | 🚫 403 | 🚫 403 | 🚫 403 |
| `GET /staff/queue` | 🚫 403 | ✅ | 🚫 403 | 🚫 403 |
| `POST /staff/requests/<id>/accept` | 🚫 403 | ✅ (unassigned, correct version) / 409 (stale version) | 🚫 403 | 🚫 403 |
| `GET /requests/<id>` (request detail) | ✅ own / 🚫 404 other Requester | ✅ unassigned or own-assigned / 🚫 404 assigned-to-other-staff | ✅ any request | ✅ any request |
| `GET /landing` (Manager/Administrator landing) | 🚫 403 | 🚫 403 | ✅ | ✅ |
| `GET /` (home redirect) | → `/requests` | → `/staff/queue` | → `/landing` | → `/landing` |
| `POST /login`, `POST /logout` | ✅ (role-agnostic; CSRF-gated) | ✅ | ✅ | ✅ |

## Notes on the two intentionally-broad cells

**`GET /requests/<id>` for Manager/Administrator is unrestricted by design**, not an oversight —
this is the service layer's documented oversight-visibility rule
(`src/persistence/request_service.py::get_request_detail`, line ~121: `role in ("Manager",
"Administrator")` bypasses the ownership/assignment check and also unlocks the requester's email).
This is correct for a Manager/Administrator who needs to review any request, but it is currently
reachable only by guessing a request's numeric id directly — there is no list screen that surfaces
other users' requests to Manager/Administrator yet (that's the deferred dashboard, FR-019/021/022
per CHG-002). Not a defect; flagging so it's a known, deliberate property rather than something
nobody can account for.

**404 vs 403 is used deliberately, not inconsistently.** A non-owning Requester or an unassigned
Staff member gets 404 (can't distinguish "exists and isn't yours" from "doesn't exist" — correct
anti-enumeration behaviour for NFR-012). Every role-mismatched operation above (wrong role
entirely, e.g. a Requester hitting `/staff/queue`) gets 403, which is the right signal there
because the route itself is role-restricted, not instance-restricted — nothing is being hidden
about a specific record's existence.

## What this does not cover

- **Comments/messaging (FR-010), later lifecycle transitions, Reject/Close, password reset,
  category/user administration** — none of these exist yet; there is no operation to test. See
  `docs/change/CHG-002-m3-delivery-slice.md`, which already formally records this as deferred
  scope, not a quietly dropped requirement.
- **Inactive/deactivated users** — every test above seeds `is_active = 1`. `require_login()` and
  every service-layer actor lookup filters on `is_active = 1`, so a deactivated account is
  rejected the same way an unauthenticated one is (redirected to `/login`), but that specific path
  (an account that exists, has the right role, but was deactivated mid-session) is not separately
  exercised by a test. Worth a follow-up case; not done here to keep this PR to what's already
  verified.
- **Concurrent-role edge cases** (e.g. a Staff member who is also somehow a Requester) don't apply
  — `schema.sql`'s `users.role` is a single column, one role per account, consistent with FR-001's
  "exactly one role" requirement (TR-026).

## Result

10/10 new route-level cases pass against the integration candidate, alongside the existing
39 (service-level and prior route-level tests) — **49/49 passing** at the time this document and
`tests/test_m3_role_operation_matrix.py` were first written (16 Oct 2026). Kept here as a
historical note, not deleted: the suite has since grown further (public registration, PR #85) to
**60/60 passing** as of the latest check — see `docs/quality/test-inventory.md` Part 6 for the
current count and the registration tests' assigned IDs. Zero regressions either time. This closes
the "Full role matrix" item in `docs/release/m3-release-evidence-summary.md`'s residual risk table
as **addressed**, not merely reviewed: every cell in the matrix above now has a passing automated
assertion behind it, run through the real HTTP route, including the previously-untested positive
case of a Staff member viewing their own already-accepted request.
