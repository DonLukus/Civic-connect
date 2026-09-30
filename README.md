# CivicConnect

Community Service Request Management Platform.
SEN381 Software Engineering 381 (NQF 8), Belgium Campus ITversity, 2026.

| | |
|---|---|
| **Current baseline** | PED v1.0 (M1) + ADR-001..ADR-004 (M2, in progress) |
| **Milestone** | M1 complete · M2 (Architecture, Design & Engineering Decisions) underway |
| **Team** | Masego (Workstream A) · Don (Workstream B) · Emile (Workstream C) |
| **Governing document** | SEN381 CivicConnect Master Project Brief v1.1 |

## What this project is

An organisation currently manages service requests across email, telephone, WhatsApp, spreadsheets
and paper. No channel holds the whole record and none enforces a lifecycle, so requests are
duplicated or lost, requesters cannot see progress, ownership is unclear, status changes are not
attributable and reporting is manual.

CivicConnect replaces that with one controlled record with an enforced lifecycle and an immutable
audit trail — without creating an unsustainable technical, operational or financial burden.

## Status: what actually exists right now

This is a PoC-level M2 slice, not a finished product. Concretely:

- **Traced end to end:** "Citizen submits a service request" (FR-005, FR-006) — a working web form
  through a validating domain service to a database, with a passing automated test.
- **Also implemented (not yet wired to a UI):** staff accepting a request under optimistic
  concurrency control (FR-014), with an immutable audit trail (FR-025).
- **Not built yet:** authentication (FR-001–004 — the app currently stands in a fixed demo user,
  see Known limitations), the staff queue, notifications, reporting, and everything else in the
  M1 scope baseline. `ADR-001` (stack/architecture) is **Proposed, not Accepted** — see below.

## Prerequisites and versions

Exact versions, verified against PyPI's published metadata (not asserted from memory) on
2026-09-30 — see `docs/decisions/technology-versions.md`:

- Python 3.11 (proposed — not yet confirmed on the Belgium Campus desktop platform, CN-07)
- Flask 3.1.3 (BSD-3-Clause)
- pytest 9.1.1 (MIT)

## Setup and run

```bash
pip install -r requirements.txt
python -c "
import sqlite3
conn = sqlite3.connect('civicconnect.sqlite')
conn.executescript(open('src/persistence/schema.sql').read())
conn.execute(\"INSERT INTO users (email, password_hash, role, is_active) VALUES ('demo@example.com', 'x', 'Requester', 1)\")
conn.execute(\"INSERT INTO categories (name, target_resolution_hours, is_active) VALUES ('Utilities', 48, 1)\")
conn.commit()
"
python -m src.web.app
```

Then open `http://127.0.0.1:5000/requests/new`.

## Running the tests

```bash
python -m pytest tests/ -v
```

7 tests, all passing as of 2026-09-30: request submission (FR-005/006, including the mandatory-field
and controlled-category negative cases, and the full web route), and staff acceptance under
concurrent-write protection (FR-014). Also runs automatically on every PR touching `src/` or
`tests/` — see `.github/workflows/test.yml`.

## Environment variables

Names only — see `.env.example`. Never a real value in this file or in git.

`FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`, `SESSION_COOKIE_SECURE`, `PASSWORD_HASH_ROUNDS`,
`EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_FROM_ADDRESS`, `OUTBOX_WORKER_POLL_SECONDS`.

## Repository structure

```
docs/                       All PED sections, registers and ADRs (source of truth, DEC-002/005)
  PED/                       PED sections, Markdown, compiled to docs/PED/exports/
  decisions/adr/             Architecture Decision Records (ADR-001..)
  requirements/              FR/NFR/constraints/scope/RTM as CSV
  risk/, stakeholders/, governance/, deployment/   Registers and process docs
src/
  persistence/               Data layer: schema.sql, RequestRepository, RequestService, OutboxProcessor
  web/                       Frontend: Flask app + server-rendered templates (ADR-001)
tests/                       pytest suite
requirements.txt             Pinned, verified dependency versions
.env.example                 Environment variable names (no values)
```

## Where the two accepted design patterns appear in the code

- **ADR-003, transition-table validator** (status lifecycle, FR-015–018): not yet extracted into
  its own module — currently the New→Accepted guard lives inline in
  `RequestService.accept_request` (the `WHERE status = 'New' AND assignee_id IS NULL AND version =
  ?` conditional update). Extracting it into an explicit transition table is open work, not done.
- **ADR-004, observer-style outbox fan-out** (notifications, FR-009): `RequestService.accept_request`
  writes a `request_audit` row and an `outbox_events` row in the same transaction as the status
  change; `src/persistence/outbox.py`'s `OutboxProcessor.process_pending` is the (currently
  placeholder) consumer that would dispatch email/in-app notifications without ever undoing the
  business fact if delivery fails.

## Known limitations and TODOs

- **No authentication.** `src/web/app.py` uses a fixed `REQUESTER_ID` stand-in, stated in the code
  and here rather than hidden. DEC-006 requires authenticated submission only in the real system.
- **SQLite in production is unverified and likely wrong.** `ADR-001` recommends SQLite for
  dev/test only and PostgreSQL as the production candidate — this has not been tested under an
  actual deployment yet (`docs/deployment/deployment-direction.md`).
- **A real, Windows-specific bug was found and fixed while building this**: `with
  sqlite3.connect(...) as conn:` commits/rolls back on exit but does not close the connection
  (stdlib behaviour) — left open, this held a file lock that made `os.remove()` on the database
  file fail on Windows, silently passing on more permissive filesystems. Fixed with explicit
  `try/finally: conn.close()` throughout `src/persistence/` and `tests/`. Concrete evidence for
  RSK-03/RSK-15 (unverified platform behaviour) rather than a hypothetical risk.
- **The outbox worker has no scheduling.** `OutboxProcessor.process_pending` must currently be
  invoked manually; a real trigger (loop, cron, or scheduled ping) is undecided.
- Staff queue, reporting, category/user administration, notifications delivery: not started.

## Read these first

| If you want to know | Read |
|---|---|
| The rules of this project | [`PROJECT_RULES.md`](PROJECT_RULES.md) |
| What has happened so far | [`PROJECT_HISTORY.md`](PROJECT_HISTORY.md) |
| What we are building and why | [`docs/PED/`](docs/PED/) |
| What we committed to build | [`docs/requirements/`](docs/requirements/) |
| Full requirement traceability | [`docs/requirements/RTM.csv`](docs/requirements/RTM.csv) |
| Architecture and technology decisions | [`docs/decisions/adr/`](docs/decisions/adr/) |
| What could go wrong | [`docs/risk/risk-register.csv`](docs/risk/risk-register.csv) |
| Why we chose what we chose | [`docs/decisions/decision-log.csv`](docs/decisions/decision-log.csv) |

## Baseline at a glance (M1)

- 26 functional and 14 non-functional requirements, all with sources, priorities and acceptance criteria
- 40 of 40 requirements traced in the RTM, now with M2 detail columns for the traced slice
- 12 in-scope areas, 9 explicit exclusions, 6 deferred items
- 15 managed risks, 5 assumptions, 7 forward engineering considerations
- 12 engineering decisions: 10 taken, 2 deliberately deferred; 4 ADRs since M2 (2 Accepted, 1 Proposed, 1 covering both lifecycle and notification patterns)

## Deliberately not decided yet

`ADR-001` (stack, architecture style, deployment platform) is **Proposed**, gated on a DEC-008
proof-of-concept on the actual Belgium Campus platform — see
`docs/deployment/deployment-direction.md` for what evidence is still needed. Database schema
beyond the M2 persistence spike, full UI design, API contracts and the CI/CD pipeline remain
open for the rest of M2/M3.

## Governance

`main` is protected. Substantive changes require a pull request with **two approvals from members
other than the author**. Self-approval is not accepted. See [`PROJECT_RULES.md`](PROJECT_RULES.md) §10.
Branch naming: `docs/<area>`, `feat/FR-nnn-<desc>`, `fix/<issue>-<desc>`, `chore/<desc>` for
single-requirement work; `m2/<topic>` for cross-cutting M2 work; `feature/<FR-nnn>-<desc>` for a
traced slice (see `PROJECT_RULES.md` §9).
