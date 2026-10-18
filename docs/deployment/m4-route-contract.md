# Route contract: all pages and who may use them

Supplements `m3-interface-agreement.md`, which covers the original M3 routes. Every route below
checks the role on the server; signed-out visitors are redirected to `/login` except where marked
Public. State-changing routes are POST and need the session's CSRF token (400 without it).
Failure codes are the same everywhere: 400 invalid input, 403 wrong role, 404 not found or not yours,
409 the request changed since the page loaded.

| Route | Methods | Who | Purpose (requirement) |
|---|---|---|---|
| `/login`, `/register` | GET, POST | Public | Sign in; register as a Requester (FR-002) |
| `/forgot-password` | GET, POST | Public | Ask for a reset email; same answer for any address (FR-004) |
| `/reset-password/<token>` | GET, POST | Public | Set a new password with a single-use, 60-minute link (FR-004) |
| `/logout` | POST | Any | Sign out |
| `/`, `/landing` | GET | Any / Manager, Administrator | Role home |
| `/requests/new`, `/requests` (POST) | GET, POST | Requester | Submit; duplicate warning, confirm with `confirm_duplicate=1` (FR-005, FR-006, FR-026) |
| `/requests/<id>/submitted` | GET | Requester (owner) | Receipt with reference |
| `/requests` | GET | Requester | Own requests; filters `q status category from to overdue sort dir` (FR-008, FR-012) |
| `/notifications` | GET | Requester | In-app notifications (FR-009) |
| `/staff/queue`, `/staff/queue.csv` | GET | Staff | Unassigned plus own requests; same filters, plus `assignee=me\|unassigned`; CSV export (FR-011, FR-012, FR-022) |
| `/staff/requests/<id>/accept` | POST | Staff | Self-accept a New request (FR-014) |
| `/requests/<id>` | GET | Owner, assigned or unassigned Staff, Manager, Administrator | Detail, comments, history, and the actions the viewer may take (FR-007, FR-013) |
| `/requests/<id>/status` | POST | Assigned Staff, Manager | Change status; `note` required for Resolved, Rejected and reopen (FR-015 to FR-018) |
| `/requests/<id>/assign` | POST | Manager | Assign a New request or reassign (FR-014) |
| `/requests/<id>/comments` | POST | Requester (owner), assigned Staff, Manager | Add a comment once assigned (FR-010) |
| `/manager/requests`, `/manager/requests.csv` | GET | Manager | All requests; filters incl. `assignee=<staff id>\|unassigned\|inactive`; CSV export (FR-012, FR-022) |
| `/manager/dashboard` | GET | Manager | Counts for `from` / `to` period: status, category, assignee, overdue (FR-019 to FR-021) |
| `/admin/users` | GET, POST | Administrator | List and create accounts (FR-001, FR-024) |
| `/admin/users/<id>/role`, `/admin/users/<id>/active` | POST | Administrator | Change role; deactivate or reactivate (FR-024) |
| `/admin/categories` | GET, POST | Administrator | List and add categories (FR-023) |
| `/admin/categories/<id>/update`, `/active`, `/delete` | POST | Administrator | Rename and target time; deactivate or reactivate; delete when unused (FR-023) |

The status values and who may make each change are in `src/persistence/lifecycle.py`
(proposed table: `docs/decisions/DEC-019-lifecycle-transition-table.md`).
