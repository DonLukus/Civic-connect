# Requirements map: where each requirement is built and proved

One row per functional requirement. Follow the row to the code that does it and the tests that prove it. The
wording and acceptance criteria are in [requirements/functional-requirements.csv](requirements/functional-requirements.csv);
the controlled traceability record is [requirements/RTM.csv](requirements/RTM.csv).

**Reading the status:** "Built" means the behaviour exists and these tests pass. It is **not** an acceptance
decision. The independent scope assessment ([PED section 23](PED/23-final-scope-and-project-conclusion.md), 40.00%) describes
the earlier slice and has not been redone for the work added since. Anything the tests do not cover is listed under
[Limits](#limits).

Paths: routes are in `src/web/app.py`; services are in `src/persistence/`. Tests are in `tests/`.

| FR | What a user gets | Code (service, route) | Tests |
|---|---|---|---|
| FR-001 | An Administrator creates an account with one role; the person sets their own password from a one-time link; audited | `admin_service.provision_user`; `POST /admin/users` | `test_m4_admin.py` |
| FR-002 | Anyone not signed in is sent to sign-in; passwords are bcrypt; public registration makes a Requester | `app.py` `require_login`, `login`, `register`; `user_service.py` | `test_registration.py`, `test_m3_backend_routes.py`, `test_wsgi_bootstrap.py` |
| FR-003 | Every operation is refused to the wrong role with no change | role checks in `app.py` and in every service method | `test_m3_role_operation_matrix.py`, `test_m4_workflow.py`, `test_m4_admin.py`, `test_m4_management.py` |
| FR-004 | "Forgot password": emailed single-use link that expires in 60 minutes | `password_reset.py`; `/forgot-password`, `/reset-password/<token>` | `test_m4_admin.py` |
| FR-005 | Submit a request; get a reference, status New, timestamp | `request_service.create_request`; `POST /requests` | `test_request_submission.py` |
| FR-006 | Category chosen from the active controlled list | `create_request`; `new_request.html` | `test_request_submission.py`, `test_m4_admin.py` |
| FR-007 | The Requester sees status, last change and the resolution note or rejection reason | `get_request_detail`; `request_detail.html` | `test_m4_workflow.py`, `test_requester_isolation.py` |
| FR-008 | The Requester's own requests only, newest first | `reporting.search_requests`; `GET /requests` | `test_m4_management.py`, `test_requester_isolation.py` |
| FR-009 | In-app and email notification when a request is accepted, rejected, resolved or commented | `outbox.py`; events written by `workflow.py` | `test_m4_workflow.py`, `test_m3_backend_routes.py` |
| FR-010 | Comments between Requester, assigned Staff and Manager; no contact details shown | `workflow.add_comment`; `POST /requests/<id>/comments` | `test_m4_workflow.py` |
| FR-011 | Staff see unassigned plus their own requests | `reporting.search_requests`; `GET /staff/queue` | `test_m4_management.py`, `test_m3_backend_routes.py` |
| FR-012 | Search, filter (status, category, assignee, dates, overdue) and sort; filters combine | `reporting.parse_filters`, `search_requests`; `_filters.html` | `test_m4_management.py` |
| FR-013 | Detail shows data, status, assignee, comments and ordered history | `get_request_detail`; `GET /requests/<id>` | `test_m4_workflow.py` |
| FR-014 | Staff accept; Manager assigns or reassigns (status kept, both assignees recorded) | `workflow.assign_request`, `request_service.accept_request` | `test_m4_workflow.py`, `test_request_acceptance.py` |
| FR-015 | Controlled status changes; Closed can only be reopened | `lifecycle.py` (`TRANSITIONS`, `check_transition`); `workflow.change_status` | `test_m4_workflow.py`, `test_lifecycle_validator.py` |
| FR-016 | Resolving needs a note, stored with author and time | `workflow.change_status` | `test_m4_workflow.py` |
| FR-017 | A Manager closes a Resolved request; Staff cannot | `lifecycle.MANAGER_ONLY` | `test_m4_workflow.py` |
| FR-018 | Rejecting needs a reason; the Requester is notified | `workflow.change_status` | `test_m4_workflow.py` |
| FR-019 | Dashboard counts for a period equal the stored records | `reporting.dashboard`; `GET /manager/dashboard` | `test_m4_management.py` |
| FR-020 | Breakdown by category, status and assignee; categories sum to the total | `reporting.dashboard` | `test_m4_management.py` |
| FR-021 | Overdue = open longer than the category's target | `reporting.OVERDUE_SQL`; badge in lists | `test_m4_management.py` |
| FR-022 | CSV of the filtered list: header plus one row per request | `reporting.requests_to_csv`; `/manager/requests.csv`, `/staff/queue.csv` | `test_m4_management.py` |
| FR-023 | Administrator manages categories; used ones cannot be deleted | `admin_service` category methods; `/admin/categories` | `test_m4_admin.py` |
| FR-024 | Change roles, deactivate; deactivated users cannot sign in; assignments stay visible | `admin_service.change_role`, `set_active`; `/admin/users` | `test_m4_admin.py` |
| FR-025 | Every status or assignment change is an audit entry that cannot be edited or deleted | `workflow._audit`; triggers in `schema.sql` and `migrations.py` | `test_audit_immutability.py`, `test_m4_workflow.py` |
| FR-026 | Warning when an open request exists in the same category and place | `reporting.find_possible_duplicates`; `submit_request` | `test_m4_management.py` |

## Non-functional evidence

| NFR | Where it is shown |
|---|---|
| NFR-001 list performance | `performance/load_test_staff_queue.py`; run results in [release/evidence/2026-10-18-m4/performance.json](release/evidence/2026-10-18-m4/performance.json) |
| NFR-003 credential storage | bcrypt in `user_service.py`, `admin_service.py`, `password_reset.py`; `test_registration.py` |
| NFR-004 authorisation | `test_m3_role_operation_matrix.py` and the role cases in each M4 test file |
| NFR-005 no secrets in the repository | [security/secret-scan-full-history-2026-10-18.md](security/secret-scan-full-history-2026-10-18.md); gitleaks in `.github/workflows/quality.yml` |
| NFR-006 audit | `request_audit`, `admin_audit`; `test_audit_immutability.py` |
| NFR-009 coverage and static analysis | coverage gate and Ruff, Bandit, pip-audit in `.github/workflows/quality.yml` |
| NFR-012 requester privacy | `get_request_detail`; `test_m4_final_regressions.py`, `test_requester_isolation.py` |

## Live checks

Run against a real server (not the in-process test client), results in
[release/evidence/2026-10-18-m4/](release/evidence/2026-10-18-m4/README.md):
`python -m scripts.m3_staging prepare`, `serve`, then `python -m scripts.m3_verify_live load | journeys | workflow | restart`,
`python -m scripts.m3_verify_recovery`, and `python -m scripts.check_layout_overflow` for phone-width layout.

## Limits

- The lifecycle rules beyond FR-014 to FR-018 are a proposal ([DEC-019](decisions/DEC-019-lifecycle-transition-table.md)).
- Email was exercised only against a local test mail server. There is no login or reset rate limiting yet.
- Performance was measured locally on loopback with 500 records; no hosted, cold-start or 5,000-record result exists.
- Other non-functional requirements (availability, cost, capacity, usability, accessibility) are not evidenced here; see PED section 23.
