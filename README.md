# CivicConnect

A small web application for community service requests. Residents report a problem, staff pick it up,
and every change is recorded, so nothing gets lost between email, phone calls and spreadsheets.

**Status:** Milestone 3 candidate. **Not production ready.** The Requester and Staff journeys work end
to end; Manager and Administrator tools are not built yet (see [What works today](#what-works-today)).

---

## Quick start

You need Python 3.11 or newer and Git.

```bash
git clone https://github.com/DonLukus/Civic-connect.git
cd Civic-connect
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### Option A: full demo in two commands (recommended)

Creates an isolated local database with 14 synthetic accounts and 500 sample requests. Nothing leaves
your machine and no email is sent. Needs OpenSSL, which Git for Windows includes.

```bash
pip install -r requirements-staging.txt
python -m scripts.m3_staging prepare     # once
python -m scripts.m3_staging serve       # then open http://127.0.0.1:5083/login
```

Log in with any account listed in `.m3-local/config.json` (for example `requester-0@example.test` or
`staff-0@example.test`). That file holds generated passwords and is git-ignored. Never commit it.

### Option B: run the app yourself

```bash
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export BOOTSTRAP_REQUESTER_EMAIL=you@example.test
export BOOTSTRAP_REQUESTER_PASSWORD='choose-a-password'
python -m flask --app wsgi:app run       # http://127.0.0.1:5000/login
```

On PowerShell use `$env:SECRET_KEY = "..."` instead of `export`. The app does **not** read a `.env`
file; set variables in your shell. `.env.example` only lists the names.

The database is created on first start. Without `SECRET_KEY` the app refuses to start.

---

## What works today

| Role | Can do |
|---|---|
| Anyone | Register as a Requester, sign in, sign out |
| Requester | Submit a request (title, description, category, location), get a reference number, see only their own requests with status and history, filter by status, read in-app notifications |
| Staff | See unassigned requests and their own, filter by status, open full detail, accept a request |
| Manager, Administrator | Sign in only. Dashboard, category admin and user admin are **not built**. |

Also in place: every status change writes an audit row in the same transaction, accepting is protected
against two people taking the same request, and an in-process outbox sends the "accepted" email.

**Not built yet** (deferred by [CHG-002](docs/change/CHG-002-m3-delivery-slice.md), still owed against the
baseline): assignment by Manager, statuses after Accepted, comments, password reset, search and sort, CSV
export, dashboard and overdue flags, category and user administration. Only one category ("Utilities") is
seeded. Full list: [docs/requirements/](docs/requirements/).

---

## Configuration

All settings are environment variables.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | yes | none | Signs session cookies. Random and unique per environment. |
| `DATABASE_URL` | no | `civicconnect.sqlite` | Path of the SQLite file. |
| `SESSION_COOKIE_SECURE` | no | `false` | Set `true` whenever served over HTTPS. |
| `PASSWORD_HASH_COST` | no | `12` | bcrypt cost, must be 10 to 16. |
| `BOOTSTRAP_<ROLE>_EMAIL` / `_PASSWORD` | no | none | Creates a first account for `REQUESTER`, `STAFF`, `MANAGER` or `ADMIN`. Both must be set together; password at most 72 bytes. Existing accounts are never changed. |
| `OUTBOX_WORKER_ENABLED` | no | `false` | Turns on email sending. |
| `EMAIL_SMTP_HOST`, `EMAIL_FROM_ADDRESS` | if worker on | none | SMTP server and sender. |
| `EMAIL_SMTP_PORT` | no | `587` | SMTP port. |
| `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD` | no | none | SMTP login. |
| `OUTBOX_WORKER_POLL_SECONDS` | no | `60` | How often pending email is sent. |

Never commit real values. Use your host's secret store.

---

## Tests and quality checks

```bash
python -m pytest tests/ -q                                   # 60 tests
pip install pytest-cov && python -m pytest tests/ --cov=src  # about 83% line coverage
```

GitHub Actions runs on every pull request: tests, `pip-audit`, Bandit, a full-history Gitleaks scan, a
requirements-traceability check, a pattern secret scan, Ruff (report only) and a weekly dependency audit.

Be aware: at the last check the `main` ruleset required two approvals but did **not** list these checks as
required, so a red build could still be merged. See
[docs/governance/github-governance-verification-2026-10-17.md](docs/governance/github-governance-verification-2026-10-17.md).

---

## How it is built

One Flask application, server-rendered pages, SQLite, no JavaScript framework. This is the simplest design
that meets the zero-cost constraint; the reasoning and the options considered are in
[ADR-001](docs/decisions/adr/ADR-001-architecture-and-stack-options.md) and the
[DEC-008 recommendation](docs/decisions/DEC-008-recommendation.md) (proposed, not yet approved).

```
src/web/            Flask routes, templates, stylesheet
src/persistence/    schema.sql, request and user services, status rules, email outbox
tests/              pytest suite
scripts/            local staging, live journey, load and recovery checks
performance/        NFR-001 load test
wsgi.py             entry point: creates the database, seeds accounts, starts the app
docs/               requirements, decisions, risks, governance, release evidence
```

## Security notes

- Passwords are hashed with bcrypt (cost 10 to 16). Sessions are HttpOnly, SameSite=Lax cookies; every form
  carries a CSRF token. Roles are checked on the server, and requesters can only read their own requests.
- Known gaps: no login rate limiting, no password reset, no email verification, and accounts created before
  the bcrypt change may still hold older hashes until their owner next signs in.

## Deploying

There is **no approved hosting yet**. Free hosts that reset their local disk on restart (Render's free tier
did in our test) lose SQLite data, so do not deploy publicly until durable storage is chosen. Use Option A
for demos. Current evidence and the open decision: [docs/release/m3-release-evidence-summary.md](docs/release/m3-release-evidence-summary.md),
[docs/deployment/m3-staging.md](docs/deployment/m3-staging.md). `gunicorn` does not run on Windows; the
staging launcher uses Waitress.

---

## Project documents

| Question | Where |
|---|---|
| What are we building and why? | [docs/PED/](docs/PED/) |
| What did we promise? | [docs/requirements/](docs/requirements/) |
| Why these technical choices? | [docs/decisions/](docs/decisions/) |
| What could go wrong? | [docs/risk/risk-register.csv](docs/risk/risk-register.csv) |
| How do we work? | [PROJECT_RULES.md](PROJECT_RULES.md), [PROJECT_HISTORY.md](PROJECT_HISTORY.md) |

## Contributing

University project with enforced governance: work on a branch, open a pull request, get two approvals
from members other than the author, update the RTM and `PROJECT_HISTORY.md`. Details in
[PROJECT_RULES.md](PROJECT_RULES.md).

## Team

Don (requirements, repository, backend), Masego (problem, scope, verification), Emile (risk, deployment,
documents).

## Licence

Intended as MIT, but no `LICENSE` file is committed yet. One must be added before anyone reuses the code.
