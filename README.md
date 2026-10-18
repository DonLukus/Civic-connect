# CivicConnect

Community service request management platform for SEN381, Belgium Campus ITversity, 2026.

**Team repository: [DonLukus/Civic-connect](https://github.com/DonLukus/Civic-connect).** Check `git remote -v` before using a checkout or reporting its status; similarly named repositories are not interchangeable.

Quick links: [Status](#current-status) | [Features](#purpose-and-implemented-scope) | [Stack](#technology-stack) | [Setup](#local-setup) | [Configuration](#environment-configuration) | [Security](#security-controls-and-limits) | [Tests](#tests-and-evidence) | [Deployment](#staging-and-deployment) | [Structure](#project-structure) | [Contributing](#contributing-and-support) | [Team](#team-responsibilities)

## Current status

| Area | Position |
|---|---|
| M3 evaluation slice | Implemented, reviewed and merged through PR #85, including the role-matrix/RTM work from #86 |
| PED | Continuing M1/M2 document through M3 section 22; corrected full export merged through #89/#90 |
| Decisions | #88 recorded DEC-013 through DEC-018; ADR-001/007 remain Proposed and DEC-008 remains Deferred |
| Automated suite | 271 pytest cases: service, in-process web/integration, role and migration checks; not browser tests |
| Staging | Isolated local Waitress/SQLite environment with synthetic users and a local SMTP sink |
| Public production | **NOT READY** |

Status reconciled 18 October 2026 against main `af2f5456a9a940f6c9a020db5cd5fe5e4889219d` (PR #91). This README correction does not create a new release approval, milestone signature or requirement acceptance. See [PED section 22](docs/PED/22-m3-construction-verification-release.md) and the dated update in the [release evidence summary](docs/release/m3-release-evidence-summary.md).

## Purpose and implemented scope

CivicConnect aims to replace fragmented requests across email, telephone, WhatsApp, spreadsheets and paper with a controlled request record, clear ownership and attributable changes.

The application now implements every functional requirement in the baseline (FR-001 to FR-026):

- **Everyone:** register as a Requester, sign in and out, reset a forgotten password by emailed single-use link.
- **Requester:** submit a request (controlled category, duplicate warning at the same place), see only their own requests with status, last change and any resolution note or rejection reason, search, filter and sort them, comment once a staff member is assigned, and receive in-app and email notifications when a request is accepted, rejected or resolved or when staff comment.
- **Staff:** a queue of unassigned and own requests with search, filters, sort, overdue flags and CSV export; accept a request; move it through In Progress, On Hold, Resolved (resolution note required) or Rejected (reason required); comment.
- **Manager:** all requests with the same tools; assign and reassign; close resolved requests; reopen closed ones with a reason; an activity dashboard (counts by status, category and assignee for a period) and overdue identification from each category's configured target time.
- **Administrator:** create accounts with exactly one role (the person sets their own password through a one-time link), change roles, deactivate and reactivate accounts, and manage the category list (create, rename, target time, deactivate, delete only when unused). Every change is audited.
- **Throughout:** every status or assignment change writes an audit row in the same transaction; the audit tables cannot be edited or deleted through the application; stale pages are refused by a version check; the role is checked on the server for every operation.

Three things to know before relying on it:

- The lifecycle rules beyond what FR-014 to FR-018 state (who may reopen, whether Staff may reject, whether Rejected is final) are a **proposal** awaiting the team's decision: [DEC-019](docs/decisions/DEC-019-lifecycle-transition-table.md).
- The 40.00% scope assessment in [PED section 23](docs/PED/23-final-scope-and-project-conclusion.md) describes the earlier delivered slice. This work is new, has not been through that independent assessment, and changes no acceptance status by itself.
- Email is only exercised against a local test sink, and there is no login or password-reset rate limiting yet.

[CHG-002](docs/change/CHG-002-m3-delivery-slice.md) records the scoped evaluation proposal; its dated pending wording is followed by the recorded decisions in PED section 22 and the release-summary update. Deferred baseline obligations remain visible and are not marked fulfilled by narrowing the demonstration. [Requirements and original acceptance criteria](docs/requirements/) and the [RTM](docs/requirements/RTM.csv) remain the controlled references.

## Runtime and data

The implementation uses Python, server-rendered Flask, SQLite, bcrypt and a transactional request/audit/outbox design. Pinned application dependencies are in [requirements.txt](requirements.txt); CI uses Python 3.11. Gunicorn is for Unix hosting and does not run on Windows. Local simulated staging uses the separate [staging requirements](requirements-staging.txt) and Waitress.

SQLite records persist in the configured local file across process restarts; that is not proof of hosted durability. No PostgreSQL implementation or final production-platform acceptance is claimed. Fresh accounts use bcrypt; successful login upgrades supported legacy hashes, but dormant legacy accounts still need an explicit migration/reset disposition.

## Technology stack

| Component | Current implementation | Version/source |
|---|---|---|
| Language | Python | 3.11 used by CI; earlier project checks also recorded 3.12/3.14 environments |
| Web framework and UI | Flask, Jinja templates, CSS | Flask 3.1.3 in `requirements.txt` |
| Database | SQLite through Python's `sqlite3` | SQLite library supplied with the installed Python; PostgreSQL remains a candidate |
| Password hashing | bcrypt; Werkzeug for checking supported legacy hashes before upgrade | bcrypt 5.0.0 in `requirements.txt` |
| Automated tests | pytest | 9.1.1 in `requirements.txt` |
| Local simulated staging | Waitress and aiosmtpd | 3.0.2 and 1.4.6 in `requirements-staging.txt` |
| Unix WSGI server candidate | Gunicorn | 26.2.0 in `requirements.txt`; not usable on Windows |
| CI and analysis | GitHub Actions, pytest, Ruff, Bandit, pip-audit and Gitleaks | Configuration in `.github/workflows/`; tool results apply to their recorded run |

Dependency pins describe the checkout, not final platform acceptance. See [ADRs](docs/decisions/adr/) and the [decision log](docs/decisions/decision-log.csv) for decision status.

## Local setup

Use only synthetic data. Do not expose this demonstration to real users or put credentials in Git.

Prerequisites: Git and Python 3.11 or later with pip. Use an unused checkout folder and a separate local database.

### Windows (PowerShell)

```powershell
git clone https://github.com/DonLukus/Civic-connect.git
cd Civic-connect
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:DATABASE_URL = Join-Path (Get-Location) "civicconnect-local.sqlite"
$env:SESSION_COOKIE_SECURE = "false"
$env:PASSWORD_HASH_COST = "12"
$env:OUTBOX_WORKER_ENABLED = "false"

python -m flask --app wsgi:app run --host 127.0.0.1 --port 5000
```

### Linux and macOS (Bash)

Use a `python3` installation satisfying the same prerequisite:

```bash
git clone https://github.com/DonLukus/Civic-connect.git
cd Civic-connect
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DATABASE_URL="$PWD/civicconnect-local.sqlite"
export SESSION_COOKIE_SECURE=false
export PASSWORD_HASH_COST=12
export OUTBOX_WORKER_ENABLED=false

python -m flask --app wsgi:app run --host 127.0.0.1 --port 5000
```

These Bash instructions express the same environment and application startup as the Windows path. They are not evidence of a fresh Linux/macOS walkthrough; use the project's recorded platform checks and verify your actual environment.

Open `http://127.0.0.1:5000/register` to create a synthetic Requester, then sign in at `/login`. `wsgi.py` initialises the schema and the default Utilities category, which is the only seeded category; an Administrator adds and manages the rest under Categories. The application does not read a `.env` file because no dotenv package is installed, so these commands set the environment directly; [.env.example](.env.example) only lists the variable names. Keep the generated signing key stable for the local session; a new key invalidates old sessions.

Privileged demo users can be provisioned through the optional bootstrap environment variables named in `.env.example`. For the complete Staff/notification demonstration with 14 synthetic accounts and 500 sample requests, install `requirements-staging.txt` (OpenSSL is needed; Git for Windows includes it), run `python -m scripts.m3_staging prepare` once and then `python -m scripts.m3_staging serve`; generated logins are in the git-ignored `.m3-local/config.json`. Follow the isolated [M3 staging runbook](docs/deployment/m3-staging.md), which generates synthetic fixtures and a local STARTTLS mail sink. Do not run its fixture generator against an existing database. Public HTTPS and external mail delivery require separate verification.

## Environment configuration

`.env.example` is the controlled list of variable names; actual values belong in the process environment or an explicitly configured local loader. Keep secrets, databases and `.m3-local/` out of Git. The examples above disable mail delivery and use loopback HTTP.

| Variable | Meaning and current behaviour |
|---|---|
| `SECRET_KEY` | Required Flask session-signing secret; use a random private value per environment. Do not print or commit it. |
| `DATABASE_URL` | SQLite **file path** consumed by the current code; defaults to `civicconnect.sqlite` in `wsgi.py`. Setting a PostgreSQL URL does not implement a PostgreSQL adapter. |
| `SESSION_COOKIE_SECURE` | `false` for loopback HTTP; `true` requires HTTPS. HttpOnly and SameSite=Lax are configured in the app. |
| `PASSWORD_HASH_COST` | bcrypt cost, default 12; code accepts 10 through 16. |
| `BOOTSTRAP_REQUESTER_EMAIL`, `BOOTSTRAP_REQUESTER_PASSWORD` | Optional pair to create a synthetic Requester if absent. Omit both when using public registration. |
| `BOOTSTRAP_STAFF_EMAIL`, `BOOTSTRAP_STAFF_PASSWORD` | Optional pair to provision a Staff demo account. |
| `BOOTSTRAP_MANAGER_EMAIL`, `BOOTSTRAP_MANAGER_PASSWORD` | Optional pair to provision a Manager demo account. |
| `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` | Optional pair to provision an Administrator demo account. |
| Bootstrap password length | Any bootstrap password longer than 72 UTF-8 bytes (bcrypt's limit) makes startup refuse to run. |
| `OUTBOX_WORKER_ENABLED` | Default `false`; `true` starts the in-process notification loop and requires SMTP host/sender settings. |
| `OUTBOX_WORKER_POLL_SECONDS` | Default 60; positive integer interval between processing passes. |
| `APP_BASE_URL` | Public address used in password-reset emails (default `http://127.0.0.1:5000`; no trailing slash needed). Set it to the real HTTPS address when deployed. |
| `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT` | SMTP host and port; port defaults to 587. The implementation calls STARTTLS. |
| `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD` | Optional SMTP login; a username requires a password. Local staging uses its separate synthetic sink configuration. |
| `EMAIL_FROM_ADDRESS` | Sender address required for delivery. |
| `FLASK_ENV` | Present in the template; the setup instructions configure the launch explicitly with Flask CLI. It is not a substitute for reviewing deployment/security settings. |

Each bootstrap email/password must be supplied together. Startup does not reset an existing account's password, and it refuses a matching email with a different role. This is only for first-time demo accounts; day-to-day account management is done by an Administrator under Users. Check [wsgi.py](wsgi.py) and the [interface agreement](docs/deployment/m3-interface-agreement.md) for the actual contract.

## Security controls and limits

- Authenticated sessions are checked against an active stored user; route and service checks enforce role/record boundaries for the implemented operations.
- State-changing forms require a session-bound CSRF token. Missing/invalid tokens are rejected; logout is a POST operation. See the CSRF and logout regressions in `tests/`.
- Fresh registered/bootstrap passwords are bcrypt hashes, never plaintext database values. Registration enforces an eight-character minimum and bcrypt's 72-byte UTF-8 limit. Dormant legacy hashes still need a migration/reset decision.
- Request acceptance uses a version check and transactional state/audit/outbox writes. The current audit records do not establish every later lifecycle or production tamper-resistance requirement.
- Keep signing keys and bootstrap/SMTP credentials private. Inspect the exact CI secret/static/dependency scan result rather than interpreting a green run as a complete security assessment.

Login/signup rate limiting, email verification, production SMTP/TLS assurance and outbox crash recovery remain outstanding. The local SMTP sink is controlled test transport, not proof of delivery to an external inbox. See the [release risks](docs/release/m3-release-evidence-summary.md) and [technical debt](docs/quality/technical-debt-register.md).

## Tests and evidence

```powershell
python -m pytest tests/ -q
```

Run one area or case while investigating:

```sh
python -m pytest tests/test_request_acceptance.py -v
python -m pytest tests/test_request_submission.py::test_create_request_succeeds_with_valid_data -v
```

For an optional local coverage report, install the coverage plugin in the development environment:

```sh
python -m pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

Inspect `htmlcov/index.html` and the measured service-layer coverage before claiming NFR-009. The report is ignored by Git; these commands do not assert that coverage has already met its threshold.

The finalisation review candidate contains 62 cases; the merged pre-finalisation suite contains 60. The earlier 15-, 18-, 39- and 50-case reports are historical snapshots. Flask test-client cases are in-process functional/integration tests. Separate live HTTP journeys and supplementary browser walkthrough evidence are recorded; no persistent browser automation suite is claimed.

The recorded NFR-001 local warm-instance measurement used 10 Staff users, 500 filtered records and 300 seconds: 8,503 successful requests, zero failures, p95 0.422 seconds. Load/restart/backup evidence predates registration and was not silently relabelled as a rerun on later revisions. It is not hosted availability, cold-start, browser-rendering or production-capacity evidence.

- [Release evidence and residual risks](docs/release/m3-release-evidence-summary.md)
- [Test inventory](docs/quality/test-inventory.md), [role-operation matrix](docs/quality/role-operation-matrix.md) and [verification handoff](docs/quality/m3-verification-handoff.md)
- [Route/UI contract](docs/deployment/m3-interface-agreement.md)
- [Quality, secret-scan and traceability workflows](.github/workflows/)

Evaluate the exact commit and run, not only a test count or green badge. Passing CI does not establish all 40 requirements or production readiness.

## Staging and deployment

For the reproducible supervised demonstration, use [M3 isolated staging](docs/deployment/m3-staging.md). It documents fixture preparation, separate server/mail processes, live journeys, the five-minute load run and restart checks. Preserve later results in a new evidence directory instead of overwriting historical reports.

Render remains historical proof-of-concept/platform evidence under DEC-008, not an approved production deployment recipe. Follow [deployment direction](docs/deployment/deployment-direction.md) as a dated proposal and the [release summary](docs/release/m3-release-evidence-summary.md) for current limits. Verify durable storage across restart/redeploy, external SMTP/TLS, host compatibility, cost and recovery before selecting a hosted release configuration. An absolute SQLite path alone does not provide persistence.

Deploy only an explicitly reviewed commit through the agreed process. Do not bypass the PR workflow with a direct push to main. Gunicorn is a Unix server option; the local Windows staging guide uses Waitress. The Flask development server in quick start is for loopback development.

## Project structure

```text
Civic-connect/
|-- src/
|   |-- persistence/
|   |   |-- schema.sql              # SQLite schema
|   |   |-- request_service.py      # Request rules, queries and acceptance
|   |   |-- request_repository.py   # Earlier repository implementation
|   |   |-- user_service.py         # Requester registration, password rules
|   |   |-- workflow.py             # Status changes, assign/reassign, comments (one transaction each)
|   |   |-- reporting.py            # Search/filter/sort, dashboard, overdue, CSV, duplicate check
|   |   |-- admin_service.py        # Accounts, roles and categories (Administrator only)
|   |   |-- password_reset.py       # Single-use, expiring reset links
|   |   |-- migrations.py           # Versioned schema upgrades, applied when a service starts
|   |   |-- lifecycle.py            # Status transition table and role rules (DEC-019, proposed)
|   |   `-- outbox.py               # Notification claiming and delivery
|   `-- web/
|       |-- app.py                  # Flask routes, sessions and CSRF
|       |-- templates/              # Login, registration and scoped role pages
|       `-- static/                 # Styles
|-- tests/                          # pytest service/web/regression cases
|-- scripts/                        # Local staging, live and recovery harnesses
|-- performance/                    # Staff queue load scenario
|-- tools/                          # Continuing PED PDF builder
|-- docs/
|   |-- PED/                        # Numbered sources and compiled review exports
|   |-- requirements/               # Baseline requirements, scope and RTM
|   |-- decisions/                  # Decision log and ADRs
|   |-- deployment/                 # Interface and staging runbooks
|   |-- quality/                    # Inventory, role matrix, defects and debt
|   |-- release/                    # Release summary and dated evidence
|   |-- governance/                 # AI register and governance records
|   `-- risk/                       # Risk and assumption registers
|-- .github/                        # Workflows and contribution templates
|-- wsgi.py                         # Schema/bootstrap and WSGI entrypoint
|-- requirements.txt                # Pinned application/test dependencies
|-- requirements-staging.txt        # Optional Waitress/local SMTP dependencies
|-- requirements-docs.txt           # Optional PED build dependencies
|-- .env.example                    # Configuration names, no secret values
|-- PROJECT_RULES.md
|-- PROJECT_HISTORY.md
`-- README.md
```

## Remaining work

Public production remains NOT READY. Outstanding behaviour and assurance include:

- Independent review and re-assessment of the work above against the original acceptance criteria, and a decision on DEC-019.
- Login and reset rate limiting, revoking sessions after a password reset, durable hosted storage, external SMTP/TLS, outbox recovery/idempotency, dormant legacy hashes and schema-compatible rollback.
- Sustained availability, cold-start, capacity and accessibility evidence; daily backup scheduling/retention beyond the recorded local restore drill.
- Final technology/hosting decisions and evidence-backed disposition of remaining acceptance criteria.

Use the release summary, RTM, [defect register](docs/quality/defect-register.csv) and [technical-debt register](docs/quality/technical-debt-register.md) for the authoritative details and owners. A successful scoped demonstration is not acceptance of the whole product baseline.

## Governance and contributions

Work on a branch and open a PR. Substantive changes require two approvals from different non-author people, resolved review discussions, updated affected records and an AI-assistance declaration. Two accounts owned by one person are not two independent reviewers. Follow [PROJECT_RULES.md](PROJECT_RULES.md); do not push feature changes directly to main or stage temporary review files indiscriminately.

Main has active protection rulesets requiring a PR and two approvals. The [17 October governance verification](docs/governance/github-governance-verification-2026-10-17.md) records narrower gaps: stale-approval dismissal is off and required-status-check lists are empty. Last-push approval and conversation resolution are on. Bypass actors and platform secret-scanning settings remain unverified without administrator evidence. The verification PR records discrepancies; it does not fix settings or prove every historical approval was independent.

## Contributing and support

1. Read the rules, history, PED and affected requirement/acceptance records. For a defect, include reproduction, expected/actual behaviour, impact and related IDs in the project issue or PR; use the existing templates.
2. Work on a small branch following project conventions: `docs/<area>`, `feat/FR-nnn-<description>`, `fix/<issue>-<description>` or `chore/<description>`. Preserve existing identifiers.
3. Make focused commits such as `docs(readme): clarify local setup` or `fix(<area>): describe the correction`, referencing the real issue/artefact where applicable. Inspect `git status` and stage named project files rather than temporary review downloads or credentials.
4. Run checks appropriate to the change. Update affected RTM/register entries, declare material AI assistance and add the history entry. Do not change acceptance status merely because code or text changed.
5. Open a PR using the template. Don and Masego independently review Emile-authored changes; the other two non-author people review changes authored by a different member. Record actual findings, resolve discussions and inspect CI on the final revision before merging.

For help, start with the [interface contract](docs/deployment/m3-interface-agreement.md), [staging guide](docs/deployment/m3-staging.md) and the relevant defect/debt record. Raise remaining questions through the repository's [issues](https://github.com/DonLukus/Civic-connect/issues) or the associated PR, with synthetic reproduction data and no credentials.

## Project records and responsibilities

| Topic | Source |
|---|---|
| Rules, ownership and progressive history | [Project rules](PROJECT_RULES.md), [history](PROJECT_HISTORY.md) |
| Continuing PED and reproducible PDF build | [PED index](docs/PED/README.md), [full review PDF](docs/PED/exports/PED_v3.0-review.pdf) |
| Original scope and requirements | [Controlled requirements](docs/requirements/), [RTM](docs/requirements/RTM.csv) |
| Architecture and decisions | [ADRs](docs/decisions/adr/), [decision log](docs/decisions/decision-log.csv) |
| Risk and AI accountability | [Risk register](docs/risk/risk-register.csv), [AI register](docs/governance/ai-usage-register.csv) |

## Licence

No licence has been chosen and no `LICENSE` file is committed, so all rights are reserved by default. The team, and the university if it has a claim on coursework, must decide before anyone reuses the code.

## Team responsibilities

| Member | Current M3 responsibility recorded in document control |
|---|---|
| Don (Workstream B) | Architecture, core implementation and configuration |
| Masego (Workstream A) | Verification and traceability |
| Emile (Workstream C) | Staging, performance, release evidence and PED assembly |

These describe the M3 allocation; the historical M1 ownership in PROJECT_RULES is retained. Authorship and actual review evidence remain in PRs, history and the AI register. All three remain accountable for the whole project.

The full PED export includes all existing numbered sources and preserves historical signatures and dates. Section 18 has no source and remains an explicit gap. Record the actual submission date and final documentation identifier when submitting; this README supplies neither a signature nor a submission claim.


## Finalisation review candidate - Group U

[PED section 23](docs/PED/23-final-scope-and-project-conclusion.md) continues the same document into a v4.0 review candidate, with the original 40-AC scope assessment, current verification and remaining gates. The acceptance-quick-wins candidate adds Manager filtered CSV export (FR-022), duplicate warning/confirm/cancel (FR-026), stronger field-level validation and a measured mobile overflow correction. Proposed scope completion is **47.50% (19/40)**, below the 80% target and pending independent review/merge; the supervised slice does not remove missing original commitments. The prior DEF-006/CI evidence remains in the [18 October verification summary](docs/release/evidence/2026-10-18/verification-summary.json), and the final local 96-case, 81.28% persistence-coverage, browser and five-participant human evidence is in [acceptance quick wins](docs/release/evidence/2026-10-18/acceptance-quick-wins.md). Public production remains NOT READY. Final team release decision, assessed documentation reference and actual Moodle submission are pending. Deadline: 18 October 2026, provided by Emile.
