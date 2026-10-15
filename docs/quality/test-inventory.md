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
