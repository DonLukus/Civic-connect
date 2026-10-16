# M3 Test Inventory and Gap Analysis

Owner: Masego (CivicConnect M3 Verification, Black-Box Testing and Traceability Lead).
First deliverable per the M3 scope brief — produced before any new test is written, so the team
sees the real gaps before anyone assumes they're closed.

**Tested commit:** `main` as of this branch's base, plus this branch's own two new tests —
`python -m pytest tests/ -v` run locally, Windows, Python 3.13. **18 of 18 tests passed**
(16 pre-existing + TST-017/TST-018 added below). This inventory reflects what that run actually
covers, not what the M3 scope describes as a destination.

## Part 1 — Existing tests, mapped

| TST ID | Test | File | Requirement(s) | Level | Technique | Risk |
|---|---|---|---|---|---|---|
| TST-001 | `test_can_accept_when_new_and_unassigned` | `test_lifecycle_validator.py` | FR-014, FR-015 | Unit | Equivalence partitioning (state × assignment) | Illegal lifecycle transition |
| TST-002 | `test_cannot_accept_when_already_assigned` | `test_lifecycle_validator.py` | FR-014, FR-015 | Unit | Equivalence partitioning (negative) | Double-assignment |
| TST-003 | `test_cannot_accept_when_not_new` | `test_lifecycle_validator.py` | FR-015 | Unit | Equivalence partitioning across all non-New states | Illegal transition from any wrong state |
| TST-004 | `test_double_accept_rejected` | `test_request_acceptance.py` | FR-014 | Integration (service + DB) | State-transition + concurrency (optimistic lock) | **High** — race condition, double acceptance (RSK pattern: concurrent write) |
| TST-005 | `test_create_request_succeeds_with_valid_data` | `test_request_submission.py` | FR-005 | Unit/component (service + DB) | Equivalence partitioning (valid class) | Data not persisted correctly |
| TST-006 | `test_create_request_rejects_missing_title` | `test_request_submission.py` | FR-005 | Unit/component | Equivalence partitioning (invalid class) / boundary | Invalid data accepted |
| TST-007 | `test_create_request_rejects_inactive_category` | `test_request_submission.py` | FR-006 | Unit/component | Equivalence partitioning (negative) | Controlled-category bypass |
| TST-008 | `test_create_request_rejects_unknown_category` | `test_request_submission.py` | FR-006 | Unit/component | Equivalence partitioning (negative, FK) | Referential-integrity bypass |
| TST-009 | `test_web_submit_request_end_to_end` | `test_request_submission.py` | FR-005, FR-006 | Black-box functional (Flask test client, in-process) | Scenario-based | **High** — core traced-slice flow broken |
| TST-010 | `test_web_submit_request_rejects_invalid_category` | `test_request_submission.py` | FR-006 | Black-box functional | Equivalence partitioning (negative) | 500 instead of a handled rejection |
| TST-011 | `test_unauthenticated_submission_does_not_write` | `test_request_submission.py` | FR-002, NFR-004 | Black-box, negative/security | Negative/security testing | **High** — auth bypass |
| TST-012 | `test_bad_password_does_not_authenticate` | `test_request_submission.py` | FR-002 | Black-box, negative/security | Negative/security testing | **High** — auth bypass |
| TST-013 | `test_missing_csrf_does_not_write` | `test_request_submission.py` | NFR-005 (security posture) | Black-box, negative/security | Negative/security testing | **High** — CSRF vulnerability |
| TST-014 | `test_browser_favicon_request_does_not_invalidate_login_csrf` | `test_request_submission.py` | Regression (login/favicon/CSRF defect, see PR #76) | Black-box, regression | Regression testing | Session invalidation recurring |
| TST-015 | `test_service_rejects_staff_request_creation` | `test_request_submission.py` | FR-003 | Unit/component | Equivalence partitioning (role-based, negative) | **High** — authorisation bypass |
| TST-016 | `test_wsgi_login_save_and_repeat_bootstrap` | `test_wsgi_bootstrap.py` | FR-002, FR-005, NFR-011 (bootstrap idempotency) | Integration (full WSGI entrypoint + DB) | Scenario-based | Deployment bootstrap failure on restart |
| TST-017 | `test_requester_cannot_open_another_requesters_confirmation_page` | `test_requester_isolation.py` (new, this branch) | FR-008, NFR-012 | Black-box functional | Negative/security testing (role/ownership partitioning) | **High** — requester data exposed to another requester |
| TST-018 | `test_owning_requester_can_open_own_confirmation_page` | `test_requester_isolation.py` (new, this branch) | FR-007 | Black-box functional | Equivalence partitioning (positive control case) | Isolation fix breaking the legitimate owner's access |

**Note on "black-box functional" above:** every one of these runs through Flask's in-process test
client, calling real routes with real HTTP verbs and asserting on real responses — genuinely
black-box against the route layer. None of them is a **browser** E2E test (no real browser, no
network hop, no rendered-DOM assertion). The M3 brief explicitly asks these to be distinguished —
see the gap list below.

## Part 2 — Tally against the M3 minimum

| Minimum | Required | Actual | Met? |
|---|---|---|---|
| Meaningful cases overall | ≥15 | 18 | ✅ |
| Unit/component | ≥5 | 8 (TST-001/002/003/005/006/007/008/015) | ✅ |
| Black-box functional | ≥5 | 8 (TST-009/010/011/012/013/014/017/018) | ✅ |
| API/integration | ≥3 | 3 (TST-004, TST-009, TST-016) | ✅, but thin — see gap note |
| E2E/system | ≥2 | **0 confirmed** (see gap note) | ❌ |
| Negative/failure/unauthorised | ≥3 | 11 (TST-002/003/006/007/008/010/011/012/013/015/017) | ✅ |
| High-priority requirement/risk | ≥5 | 10 (every row flagged High above) | ✅ |
| Black-box techniques (≥2 distinct) | ≥2 | 3 (equivalence partitioning, state-transition, negative/security) | ✅ |

**Seven of eight minimums are met by what exists after this branch.** The one real shortfall, and
one soft one, below.

## Part 3 — Gaps, honestly

### Gap 1 — No genuine E2E/system test exists yet (minimum not met)
TST-009 and TST-016 are the closest candidates, but both run through Flask's test client, not a
real browser. The M3 brief itself requires distinguishing these ("Include real browser evidence
where needed... Clearly distinguish Flask test-client tests from browser E2E tests"). Closing
this needs either a browser-automation tool (not currently in `requirements.txt`) added and
agreed with Don, or an explicit team decision that in-process Flask-client tests are accepted as
the E2E tier for M3 — and if so, that needs recording as a decision, not assumed silently.

### Gap 2 — The two required integrated journeys cannot be written yet
> 1. Requester signs in, submits and finds their request/status.
> 2. Staff signs in, filters the queue and accepts; the Requester sees the resulting status and
>    required notification.

Checked `src/web/app.py` and `src/web/templates/` directly: routes exist for `login`, `logout`,
`new_request_form`, `submit_request`, and a single-request `request_submitted` confirmation page
(owner-checked, 404s for another requester — this part of Journey 1 **is** testable now). There
is **no route or template for**:
- Viewing a list of the requester's own requests (FR-008) — journey 1's "finds their request"
  step has nothing to revisit after the confirmation page closes.
- A staff queue, with or without status filtering (FR-011, FR-012).
- A request-detail view (FR-013).
- Accepting a request through the web (only the service-layer `RequestService.accept_request` is
  tested directly, in `test_request_acceptance.py` — never through an HTTP route).
- Any Manager or Administrator screen at all.

**This blocks Journey 2 entirely and half of Journey 1.** This is a dependency on Don (routes) and
Emile (templates), not something to invent on the verification side. Flagging now, per the brief's
own instruction, rather than after building fake coverage around it.

### Gap 3 — API/integration count is thin and architecturally a bit of a stretch
The 3 that count (TST-004, TST-009, TST-016) are service+DB or WSGI+DB integration — there is no
JSON API in this architecture (ADR-001: server-rendered, single deployable unit), so "API testing"
in the REST-contract sense doesn't apply here. Worth stating plainly rather than implying contract
tests exist that don't.

### Gap 4 — No defect register existed
Scaffolded at `docs/quality/defect-register.csv`, backfilled with the two real defects already
found and fixed this milestone (favicon/CSRF session-clearing, the shadowed duplicate test name —
both in PR #76).

### Gap 5 — No static/code-quality CI check existed
Added `.github/workflows/lint.yml` (ruff 0.17.0, MIT, verified against PyPI - not added to
`requirements.txt`, to avoid touching Don's dependency file). First run against current `main`
found **12 findings**, disposition below. Configured **non-blocking** for now — making it
mandatory is a team call once the findings have owners, not something to force by turning CI red
on day one.

| Finding | Count | Severity | Disposition |
|---|---|---|---|
| `UP045` — `Optional[X]` vs `X \| None` syntax | 8 (`lifecycle.py`, `request_repository.py`) | Cosmetic | Don's files — his call whether to modernise |
| `I001` — import block unsorted | 3 (`request_service.py`, `test_request_acceptance.py`, `test_request_submission.py`) | Cosmetic | Mixed ownership — left as-is this PR, auto-fixable with `ruff --fix` whenever the owning member wants it |
| `BLE001` — blind `except Exception` in `outbox.py:23` | 1 | **Real, low severity** | Logged as **DEF-003** — could silently swallow an unexpected bug alongside the delivery failures it's meant to catch. Don's file; reported, not fixed here. |

### Gap 6 — RTM's M3 columns (`Issue/PR (M3)`, `Test ID (M3)`) were blank for every row
Filled in for the 10 requirements this inventory actually covers (see the next commit) — the
remaining 30 stay `Pending M3`, correctly, since nothing above tests them yet.

## Part 4 — What I can do now vs. what needs a handoff

**Can do now, no coordination needed:** a requester-isolation test against the one route that
already exists and already enforces it (`request_submitted`); a defect register; a static-check
workflow (new file, doesn't touch Don's existing `test.yml`/`secret-scan.yml`); RTM updates for
rows already covered above.

**Needs Don:** staff queue route, request-detail route, a web-facing accept action, requester
request-list route.

**Needs Emile:** the matching templates for all of the above, and his separate NFR-001 performance
scenario (not duplicated here).

**Needs a team decision:** whether Flask-test-client coverage satisfies the "E2E/system" minimum
for M3, or whether real browser automation is required — affects schedule and tooling (a new
dependency), so it isn't mine to decide unilaterally.

## Part 5 — Update, 16 October 2026: Don's/Emile's routes landed, gaps above closed

Everything Part 3 flagged as blocked on Don (routes) and Emile (templates) now exists on the
integration candidate `m3/emile-release-verification` (PRs #82/#83/#84 merged into it — see
`docs/release/m3-release-evidence-summary.md` for the full candidate composition). This section
assigns stable IDs to the tests that arrived with that work, per
`docs/quality/m3-verification-handoff.md` point 1, **without renumbering TST-001–018 above**.

**Count reconciliation:** `python -m pytest tests/ -v` on the candidate reports **49 passed**
(39 before this PR's additions, now +10 — see below). That total is higher than the ID count
below because `test_m3_logout.py`'s one test function is parametrized over 5 role/page
combinations (pytest counts each as a separate passing case; this inventory assigns it one ID,
consistent with "ID = test function" everywhere else in this document).

| TST ID | Test | File | Requirement(s) | Level | Technique | Risk |
|---|---|---|---|---|---|---|
| TST-019 | `test_list_requester_requests_returns_only_own_requests` | `test_m3_backend_routes.py` | FR-008 | Unit/component (service) | Equivalence partitioning | Cross-requester data leak |
| TST-020 | `test_list_requester_requests_status_filter_and_invalid_value` | `test_m3_backend_routes.py` | FR-008 | Unit/component | Equivalence + boundary (invalid filter value) | Unfiltered/incorrect list |
| TST-021 | `test_list_requester_requests_rejects_non_requester` | `test_m3_backend_routes.py` | NFR-004 | Unit/component, negative | Negative/security | Authorisation bypass |
| TST-022 | `test_staff_queue_shows_unassigned_and_own_not_other_staffs` | `test_m3_backend_routes.py` | FR-011, FR-012 | Unit/component | Equivalence partitioning | Staff sees another staff member's assigned work |
| TST-023 | `test_staff_queue_rejects_non_staff` | `test_m3_backend_routes.py` | NFR-004 | Unit/component, negative | Negative/security | Authorisation bypass |
| TST-024 | `test_request_detail_owner_can_view_non_owner_cannot` | `test_m3_backend_routes.py` | FR-013, NFR-012 | Unit/component | Equivalence partitioning | Cross-requester data leak |
| TST-025 | `test_request_detail_staff_visibility_follows_assignment` | `test_m3_backend_routes.py` | FR-013, NFR-012 | Unit/component | State-based partitioning (unassigned/assigned) | Staff sees another's assigned detail |
| TST-026 | `test_request_detail_withholds_requester_email_from_unassigned_staff` | `test_m3_backend_routes.py` | NFR-012 | Unit/component | Equivalence partitioning | Requester contact details over-exposed |
| TST-027 | `test_notifications_created_even_when_email_delivery_fails` | `test_m3_backend_routes.py` | FR-009 | Integration (service + outbox) | Scenario-based | Silent notification loss on delivery failure |
| TST-028 | `test_notifications_rejects_non_requester` | `test_m3_backend_routes.py` | NFR-004 | Unit/component, negative | Negative/security | Authorisation bypass |
| TST-029 | `test_route_request_list_allows_requester_blocks_staff` | `test_m3_backend_routes.py` | FR-008, NFR-004 | Black-box functional | Equivalence partitioning (role) | Authorisation bypass at the route |
| TST-030 | `test_route_staff_queue_allows_staff_blocks_requester` | `test_m3_backend_routes.py` | FR-011, NFR-004 | Black-box functional | Equivalence partitioning (role) | Authorisation bypass at the route |
| TST-031 | `test_route_accept_then_detail_end_to_end` | `test_m3_backend_routes.py` | FR-014, FR-013 | Black-box functional, integration | Scenario-based | Accept flow broken end-to-end, audit actor not rendered |
| TST-032 | `test_route_accept_rejects_bad_csrf_and_wrong_role` | `test_m3_backend_routes.py` | NFR-004, NFR-005 | Black-box, negative/security | Negative/security | CSRF or role bypass on accept |
| TST-033 | `test_route_notifications_and_landing` | `test_m3_backend_routes.py` | FR-009, NFR-004 | Black-box functional | Equivalence partitioning (role) | Authorisation bypass; landing page overclaiming built features |
| TST-034 | `test_static_files_not_redirected_while_signed_out` | `test_m3_backend_routes.py` | Regression | Black-box, regression | Regression testing | Static assets wrongly gated behind login |
| TST-035 | `test_logout_from_shared_navigation` (5 role/page combinations) | `test_m3_logout.py` | NFR-005 (session integrity) | Black-box, regression | Regression testing, parametrized across 5 roles | Logout CSRF broken for a given role's page, or session not actually cleared |

### New this PR — route-level role x operation matrix (TST-036–045)

Full rationale and the matrix table itself: `docs/quality/role-operation-matrix.md`. Summary:
every test above that touches role/ownership enforcement (TST-019–030) asserts against
`RequestService` directly, not the HTTP route — a route-wiring bug would not be caught. These
ten close that gap by hitting the real route as every role expected to be rejected, including
**Administrator**, which had no authorisation coverage anywhere before this (only a positive
`GET /landing` check, inside a logout-mechanics test, not an authorisation test).

| TST ID | Test | File | Requirement(s) | Level | Technique | Risk |
|---|---|---|---|---|---|---|
| TST-036 | `test_new_request_form_blocks_non_requester` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-037 | `test_submit_request_blocks_non_requester_at_route` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-038 | `test_request_submitted_blocks_non_requester_and_non_owner_roles` | `test_m3_role_operation_matrix.py` | NFR-004, NFR-012 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-039 | `test_request_list_blocks_staff_manager_administrator` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-040 | `test_notifications_blocks_staff_manager_administrator` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-041 | `test_staff_queue_blocks_requester_manager_administrator` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional, negative | Equivalence partitioning (role) | Route-level authorisation bypass |
| TST-042 | `test_accept_request_blocks_requester_manager_administrator` | `test_m3_role_operation_matrix.py` | NFR-004, FR-014 | Black-box functional, negative | Equivalence partitioning (role) + state verification | Route-level authorisation bypass, or a rejected attempt mutating state anyway |
| TST-043 | `test_landing_blocks_requester_and_staff_allows_manager_and_administrator` | `test_m3_role_operation_matrix.py` | NFR-004 | Black-box functional | Equivalence partitioning (role), both directions | Route-level authorisation bypass; Administrator never previously tested here |
| TST-044 | `test_request_detail_route_enforces_role_and_ownership` | `test_m3_role_operation_matrix.py` | FR-013, NFR-004, NFR-012 | Black-box functional | Equivalence partitioning (role x ownership x assignment) | Route-wiring bug not caught by service-only tests |
| TST-045 | `test_home_redirects_by_role` | `test_m3_role_operation_matrix.py` | NFR-004 (consistent role routing) | Black-box functional | Equivalence partitioning (role) | Wrong landing surface shown per role |

**Result:** 49/49 passing on the candidate (39 + these 10), zero regressions, ruff clean. The
"Full role matrix" residual risk in `docs/release/m3-release-evidence-summary.md` is now closed
with automated evidence, not just reviewed.
