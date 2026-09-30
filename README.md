# CivicConnect

A community service request platform.
SEN381 Software Engineering 381 (NQF 8), Belgium Campus ITversity, 2026.

| | |
|---|---|
| **Current baseline** | PED v1.0 (Milestone 1) + 6 ADRs (Milestone 2, still in progress) |
| **Milestone** | M1 is done. M2 (Architecture, Design & Engineering Decisions) is underway |
| **Team** | Masego (Workstream A) · Don (Workstream B) · Emile (Workstream C) |
| **Governing document** | SEN381 CivicConnect Master Project Brief v1.1 |

## What this project is

Right now, the organisation tracks service requests using email, phone, WhatsApp, spreadsheets
and paper. No single place holds the full record. Nothing forces requests to move through their
steps in the right order. Because of this: requests get lost or copied twice, people who make a
request can't see its progress, nobody is clearly in charge of a request, nobody can prove who
changed a request's status, and reports have to be built by hand.

CivicConnect fixes this. It gives everyone one shared, controlled record. It keeps a permanent
history of every change. It does this without costing too much money or effort to run.

## Status: what actually exists right now

This is an early, proof-of-concept slice for Milestone 2. It is not a finished product.

- **Built and tested, start to finish:** "A citizen submits a service request" (FR-005, FR-006).
  This means a real web form, a service that checks the data, and a database that stores it —
  with a test that proves it works.
- **Also built (but with no screen yet):** a staff member accepting a request. This is protected
  against two staff members accepting the same request at once (FR-014), and every change is
  written to a permanent history (FR-025).
- **Login PoC:** the request form now requires a real email/password sign-in and a Requester
  session. Account administration, password reset and the full role/operation matrix remain open.
- **Not built yet:** the staff work queue, notifications, reports, and
  everything else in the Milestone 1 plan. The choice of technology stack (`ADR-001`) is
  **Proposed, not yet final** — see below.

## What you need, and which exact versions

These exact versions were checked against PyPI (the official Python package site) on
2026-09-30, not just assumed. See `docs/decisions/technology-versions.md` for the full check.

- Python 3.11 (proposed); Python 3.14 on the Belgium Campus remote desktop ran the original
  10-test suite, but the login PoC has not yet been rerun there
- Flask 3.1.3 (the web framework — free and open-source, BSD-3-Clause licence)
- pytest 9.1.1 (the testing tool — free and open-source, MIT licence)

## How to set it up and run it

Install the pinned packages from `requirements.txt`. Set `SECRET_KEY` to a fresh random value,
and set `BOOTSTRAP_REQUESTER_EMAIL` and `BOOTSTRAP_REQUESTER_PASSWORD` to credentials for a
throwaway PoC account in your local environment or host's secret store. Do not commit those
values. Optionally set `DATABASE_URL` to a local SQLite file path; this PoC does not yet accept
a PostgreSQL URL. On a Windows desktop, use Flask's development server:

```bash
flask --app wsgi:app run
```

Open `http://127.0.0.1:5000/login`, sign in, then submit a request. `wsgi.py` creates the
schema, one active category and the PoC account on first run. It does not reset an existing
account's password on restart. Use `SESSION_COOKIE_SECURE=true` only behind HTTPS; the cookie is
HTTP-only and SameSite=Lax. Gunicorn remains the Linux-host candidate, not a Windows command.

## How to run the tests

```bash
python -m pytest tests/ -v
```

There are 15 tests, and all 15 pass locally (checked 2026-09-30). They check: submitting a request works
correctly (FR-005/FR-006), a request can't be submitted with a missing field or a bad category,
the full web form works end to end, the rule that decides when a request may move from "New" to
"Accepted" works on its own (FR-015), and two staff members can't accept the same request at the
same time (FR-014), unauthenticated access, invalid passwords, CSRF rejection and service-level
role enforcement, and the WSGI bootstrap/login/save path. The tests also run by themselves on every pull request that changes `src/` or
`tests/` — see `.github/workflows/test.yml`.

## Environment variables (settings kept out of the code)

Only the *names* of these settings are listed here — see `.env.example`. A real value must never
be written in this file or committed to git.

`FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`, `SESSION_COOKIE_SECURE`, `PASSWORD_HASH_ROUNDS`,
`EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_FROM_ADDRESS`, `OUTBOX_WORKER_POLL_SECONDS`.
The login PoC also uses `BOOTSTRAP_REQUESTER_EMAIL` and `BOOTSTRAP_REQUESTER_PASSWORD`.

## How the project is organised

```
docs/                       Every planning document, register and decision record (the source of truth)
  PED/                       The main project document, split into sections
  decisions/adr/             Architecture Decision Records — one file per big decision (ADR-001..)
  requirements/              What the system must do, as spreadsheet-style CSV files
  risk/, stakeholders/, governance/, deployment/   Other planning registers
src/
  persistence/               Talks to the database: schema.sql, and the code that reads/writes data
  web/                       The website: the Flask app and its page templates
tests/                       The automated tests
requirements.txt             The exact, checked versions of everything this project depends on
.env.example                 The names of the settings the app needs (no real values)
```

## Where the two chosen design patterns show up in the code

- **The status-change rule (ADR-003).** Lives in its own file, `src/persistence/lifecycle.py`, in
  a class called `LifecycleValidator`. It is tested on its own in
  `tests/test_lifecycle_validator.py`. Right now it only knows one rule: a request may move from
  "New" to "Accepted". The other rules in the full status list are not written yet, because
  nobody has approved exactly what they should be.
- **The notification pattern (ADR-004).** When a staff member accepts a request,
  `RequestService.accept_request` writes both a history record and a "to-do" event in the same
  database transaction. `src/persistence/outbox.py` is the piece that would later send the actual
  email or in-app message — right now it exists but has to be started by hand, not automatically.

## What's known to be missing or unfinished

- **Login is only a PoC.** It uses a single environment-provisioned Requester account with a
  hashed password. Administrator account provisioning (FR-001), the full four-role permission
  matrix (FR-003) and password reset (FR-004) are not built. ADR-007 remains Proposed pending
  team review, and the login code has not yet been exercised on the BC desktop or a host.
- **The database choice for a real, live version is not tested yet.** `ADR-001` suggests SQLite
  (a simple file-based database) for testing, and PostgreSQL (a proper server database) for the
  real version — but nobody has actually tried running it on a real host yet.
  See `docs/deployment/deployment-direction.md`.
- **A real bug was found and fixed while building this.** In Python, writing
  `with sqlite3.connect(...) as conn:` saves your changes when it finishes, but it does **not**
  close the connection. Left open like that, it can lock the database file — which broke a test
  on Windows that everyone thought was passing. It is now fixed everywhere in this project by
  closing the connection properly.
- **The "to-do" event sender has no automatic schedule.** Someone has to run it by hand for now.
- The staff work queue, reports, and managing users/categories are not started yet.

## Start here if you want to know more

| If you want to know | Read |
|---|---|
| The rules everyone on this project follows | [`PROJECT_RULES.md`](PROJECT_RULES.md) |
| What has happened on this project so far | [`PROJECT_HISTORY.md`](PROJECT_HISTORY.md) |
| What we are building, and why | [`docs/PED/`](docs/PED/) |
| Exactly what we promised to build | [`docs/requirements/`](docs/requirements/) |
| How every requirement links to evidence it was built | [`docs/requirements/RTM.csv`](docs/requirements/RTM.csv) |
| The big technical decisions, and why we made them | [`docs/decisions/adr/`](docs/decisions/adr/) |
| What could go wrong | [`docs/risk/risk-register.csv`](docs/risk/risk-register.csv) |
| Why we picked what we picked | [`docs/decisions/decision-log.csv`](docs/decisions/decision-log.csv) |

## The plan so far, in numbers (Milestone 1)

- 26 things the system must do, and 14 quality rules it must meet — each one has a reason, a
  priority, and a way to check it's done
- All 40 of those are linked to real evidence, and some now show Milestone-2 detail too
- 12 things we are building, 9 things we decided not to build, 6 things we're leaving for later
- 16 known risks being tracked, 5 assumptions, 7 things to think about ahead of time
- 12 project decisions made, 2 decisions deliberately left for later; plus 6 more technical
  decision records since Milestone 2 started (4 finalised, 2 still proposed)

## What we have deliberately not decided yet

`ADR-001` (which technology stack and hosting to use) is still **Proposed**, waiting on a real
test — logging in, saving data, and deploying it — on the actual Belgium Campus computers. See
`docs/deployment/deployment-direction.md` for exactly what evidence is still needed. The full
database design, the full look of the app, how different parts of the app talk to each other, and
an automatic build-and-test pipeline are all still open questions for later in M2 and M3.

## How the team works together (GitHub rules)

The `main` branch is protected. Any real change needs a pull request approved by **two other team
members** — nobody can approve their own work. See [`PROJECT_RULES.md`](PROJECT_RULES.md) section
10. Branch names follow a pattern: `docs/<topic>`, `feat/FR-nnn-<short description>`,
`fix/<issue>-<short description>`, or `chore/<short description>` for small, single-purpose work;
`m2/<topic>` for bigger Milestone-2 work; `feature/<FR-nnn>-<short description>` when a branch
builds one requirement all the way through (see `PROJECT_RULES.md` section 9).
