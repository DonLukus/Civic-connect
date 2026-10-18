# CivicConnect

**One place where every community service request is reported, owned, worked and closed, with a record of exactly what happened and when.**

Built by a three-person engineering team for SEN381 at Belgium Campus ITversity, 2026. Repository: [DonLukus/Civic-connect](https://github.com/DonLukus/Civic-connect).

[The problem](#the-problem) | [Our solution](#our-solution-civicconnect) | [Our approach](#our-approach) | [The journey](#the-journey-four-milestones) | [Requirements and proof](#requirements-how-we-built-to-them-and-proved-them) | [Project structure](#project-structure) | [Run it](#run-it-yourself) | [Limits](#security-and-honest-limits) | [Contributing](#governance-and-contributing)

> **New here?** [docs/START-HERE.md](docs/START-HERE.md) says where everything is. For how it is built, read the one-page [architecture](docs/ARCHITECTURE.md). To follow any requirement to its code and tests, use the [requirements map](docs/REQUIREMENTS-MAP.md).

---

## The problem

A service organisation (a municipality, a nonprofit, a facilities team) does not really have a *service request* problem. It has an **information control problem.**

Requests arrive by email, telephone, WhatsApp, spreadsheet and paper. Each channel holds a piece of the story, none holds all of it, and none enforces a process. Everything people complain about follows from that:

| What people see | What is really wrong |
|---|---|
| Requests are duplicated, overlooked or lost | There is no single record and no controlled way in |
| Residents phone to ask "where is my request?" | Status lives in people's heads, not in a system |
| Staff do not know what is theirs | Nobody is recorded as the owner |
| Nobody can say who changed what | There is no audit trail |
| Managers cannot see what is overdue | Without one state model, nothing can be counted |
| Sensitive reports are handled inconsistently | There is no boundary around who can read what |

The sponsor adds a hard constraint: **improve visibility and accountability without an unsustainable technical or financial burden.** For this project that means a recurring cost of R0.

*Source: [PED section 2, problem and business need](docs/PED/02-problem-and-business-need.md).*

## Our solution: CivicConnect

CivicConnect replaces five channels with **one controlled record**: every request gets a reference number, an owner, a status that can only change along defined rules, and an audit entry for every change.

**What each person gets**

- **Residents (Requesters)** report a problem with four short fields, get a reference, see their own request's status and history, and are notified by app and email when it moves. They never see anyone else's requests.
- **Staff** get one prioritised queue of unassigned and own work, with search, filters, sorting and overdue flags. They accept work, move it forward, comment, and must write a note to resolve or a reason to reject.
- **Managers** see every request, assign and reassign work, close resolved requests, and open a dashboard whose figures are counted straight from the stored records. They see what is outstanding, overdue and owned by whom, and can export it.
- **Administrators** create accounts (people set their own passwords through a one-time link), change roles, switch people off, and manage the list of categories and their target times.
- **Everyone is protected:** each role sees only what it should, every change is attributable, and the audit trail cannot be edited through the application.

It is deliberately small: one Flask application, one SQLite database, server-rendered pages, no paid services. That keeps it affordable, easy to run, and easy to defend line by line.

## Our approach

We treat this as an engineering project, not a coding exercise. Five habits shape everything in this repository:

| Habit | What it means in practice |
|---|---|
| **Decide with evidence** | Technology choices are scored against our own requirements and recorded as decisions with alternatives and trade-offs ([decision log](docs/decisions/decision-log.csv), [ADRs](docs/decisions/adr/)). A decision without enough evidence is recorded as *deferred*, never guessed. |
| **Trace everything** | Every stakeholder need becomes a numbered requirement with an acceptance criterion; the [RTM](docs/requirements/RTM.csv) links each to its design, code, test and evidence. |
| **Prove, don't claim** | Features are shown working by automated tests, a real-server load test, live end-to-end journeys, restart and restore drills. Evidence states the exact commit, environment and its limits. |
| **Keep it simple** | The simplest design that meets the requirement wins. One fact lives in one place; everything else links to it. |
| **Review and be honest** | Work goes through pull requests with two approvals from other people. Gaps, discrepancies and our own mistakes are written down, not hidden. |

## The journey: four milestones

| Milestone | Identity | The question it answers |
|---|---|---|
| **M1** | DEFINE | What are we committing to engineer? |
| **M2** | DECIDE & DESIGN | How will we engineer it? |
| **M3** | CONSTRUCT & VERIFY | Can we build and verify it? |
| **M4** | FINALISE & CONCLUDE | What did we finally deliver, how well does it satisfy the original commitment, and what can we conclude from the project? |

### M1: Define (baselined 8 September 2026)

We turned the brief into a controlled foundation: the [problem and stakeholders](docs/PED/03-stakeholders.md), **26 functional and 14 non-functional requirements** (40 acceptance criteria), a [scope baseline](docs/PED/04-scope-baseline.md) of 12 capabilities in, 9 deliberately out and 6 deferred, a scored [risk register](docs/risk/risk-register.csv), and the team's [working rules](PROJECT_RULES.md). No product code was written yet; every claim about quality had to carry a number and a way to check it.
Sign-off: [M1 baseline](docs/baseline/M1-baseline-signoff.md).

### M2: Decide and design

We chose the architecture before writing the product. Stack, persistence, authentication placement, the lifecycle pattern, notifications and integration were each scored and recorded ([ADR-001](docs/decisions/adr/ADR-001-architecture-and-stack-options.md) to [ADR-007](docs/decisions/adr/ADR-007-authentication-authorization-placement.md)). A thin proof-of-concept (submit a request, accept it safely when two people try at once) tested the choices. The hosting decision was **honestly deferred**: a free host lost a test request after a redeploy and we would not guess ([decision log](docs/decisions/decision-log.csv) DEC-008, [proof-of-concept log](docs/decisions/poc-log.md), [recommendation](docs/decisions/DEC-008-recommendation.md)).
Sign-off: [M2 baseline](docs/baseline/M2-baseline-signoff.md); architecture: [PED section 16](docs/PED/16-architecture-baseline.md).

### M3: Construct and verify

We built a supervised first slice (Requester and Staff journeys end to end), with a quality pipeline on every pull request (tests, Ruff, Bandit, pip-audit, secret scanning, traceability), a role-by-operation test matrix, and a reproducible local staging environment. We measured the list performance requirement (NFR-001) on a real server and recorded what we could not yet prove. The scope narrowing was a formal change request ([CHG-002](docs/change/CHG-002-m3-delivery-slice.md)).
Evidence: [release evidence summary](docs/release/m3-release-evidence-summary.md); [PED section 22](docs/PED/22-m3-construction-verification-release.md).

### M4: Finalise and conclude

We measured ourselves against the original commitment and published the result: **40.00%** of the 40 acceptance criteria satisfied by the first delivered slice (9 met, 14 partial, 17 not met), against an 80% target. We did not hide it or remove requirements to improve it. We then closed the gap in engineering terms: **all 26 functional requirements are now implemented**, with 280+ automated tests and live end-to-end checks against a running server.
Conclusion and scope assessment: [PED section 23](docs/PED/23-final-scope-and-project-conclusion.md); live verification: [M4 evidence](docs/release/evidence/2026-10-18-m4/README.md).
The 40.00% score describes the earlier slice; the newer work still needs independent re-assessment.

**Status today:** the application is feature-complete against the baseline and runs end to end. **Public production is not ready**: hosting, durable storage, real email delivery and rate limiting are open (see [limits](#security-and-honest-limits)).

## Requirements: how we built to them and proved them

**The chain.** A stakeholder need becomes a requirement with an acceptance criterion; each is designed, built, tested and evidenced, and the [RTM](docs/requirements/RTM.csv) holds the links. The [requirements map](docs/REQUIREMENTS-MAP.md) shows the same chain in one table, requirement by requirement, with the code and tests.

**Constraints we designed around**

| Constraint or conflict | How we worked around it |
|---|---|
| Recurring cost must be R0 | One deployable unit: Flask and SQLite, no paid services |
| Reporters want anonymity; management needs accountability (CF-01) | Authenticated submission only; identity shown only to the assigned Staff user, Managers and Administrators |
| Requesters want the technician's contact details; privacy forbids it (CF-04) | An in-app comment thread; no contact details shown to the Requester |
| Management wants SMS and WhatsApp alerts; no paid gateway (CF-03) | In-app and email notifications; the gap is carried openly |
| Overdue targets are not yet authorised (RSK-05) | Targets are configured per category by an Administrator; no values are invented in code |
| No live stakeholder exists | The team acts as proxy and says so; requirements are testable even where business validity is not independently confirmed |

**What we built, and how it is proved**

| Capability | Requirements | Built in | Proved by |
|---|---|---|---|
| Sign-in, roles, accounts, password reset | FR-001 to FR-004, NFR-003, NFR-004 | [app.py](src/web/app.py), [admin_service.py](src/persistence/admin_service.py), [password_reset.py](src/persistence/password_reset.py) | [role matrix tests](tests/test_m3_role_operation_matrix.py), [admin tests](tests/test_m4_admin.py) |
| Submit and track requests | FR-005 to FR-009 | [request_service.py](src/persistence/request_service.py), [outbox.py](src/persistence/outbox.py) | [submission tests](tests/test_request_submission.py), [live journeys](docs/release/evidence/2026-10-18-m4/live-system-journeys.json) |
| Work the queue and assign | FR-010 to FR-014 | [workflow.py](src/persistence/workflow.py), [reporting.py](src/persistence/reporting.py) | [workflow tests](tests/test_m4_workflow.py), [management tests](tests/test_m4_management.py) |
| Controlled lifecycle | FR-015 to FR-018 | [lifecycle.py](src/persistence/lifecycle.py) | [workflow tests](tests/test_m4_workflow.py); the table is a [proposal](docs/decisions/DEC-019-lifecycle-transition-table.md) awaiting team approval |
| Dashboard, overdue, export | FR-019 to FR-022 | [reporting.py](src/persistence/reporting.py) | [management tests](tests/test_m4_management.py) (figures compared with independent SQL) |
| Administer categories and users | FR-023, FR-024 | [admin_service.py](src/persistence/admin_service.py) | [admin tests](tests/test_m4_admin.py), [workflow journey](docs/release/evidence/2026-10-18-m4/workflow-journey.json) |
| Audit that cannot be altered | FR-025, NFR-006 | triggers in [schema.sql](src/persistence/schema.sql) and [migrations.py](src/persistence/migrations.py) | [audit tests](tests/test_audit_immutability.py) |
| Duplicate warning | FR-026 | [reporting.py](src/persistence/reporting.py) | [management tests](tests/test_m4_management.py) |
| Performance | NFR-001 | [load test](performance/load_test_staff_queue.py) | [result](docs/release/evidence/2026-10-18-m4/performance.json): 10 users, 500 records, 5 minutes, p95 0.763 s against 2.0 s |
| No secrets in the repository | NFR-005 | [CI scans](.github/workflows/quality.yml) | [full-history scan](docs/security/secret-scan-full-history-2026-10-18.md): 0 findings |
| Recoverability | NFR-011 (partial) | online backup | [restart](docs/release/evidence/2026-10-18-m4/process-restart.json) and [restore](docs/release/evidence/2026-10-18-m4/backup-restore.json) drills |

**Main evidence, in one list**

- [Requirements map](docs/REQUIREMENTS-MAP.md): every FR to its code and tests
- [M4 live verification](docs/release/evidence/2026-10-18-m4/README.md): load test, journeys, restart, restore, with commit and limits
- [Requirement traceability matrix](docs/requirements/RTM.csv) and the [requirement texts](docs/requirements/)
- [Test inventory](docs/quality/test-inventory.md) and [role-by-operation matrix](docs/quality/role-operation-matrix.md)
- [Final scope assessment](docs/PED/23-final-scope-and-project-conclusion.md), [release summary](docs/release/m3-release-evidence-summary.md), [risk register](docs/risk/risk-register.csv)

## Project structure

Everything lives in one repository. Start from the folder that matches your question.

### The application

| Where | What it is |
|---|---|
| [src/web/app.py](src/web/app.py) | Every page and form: sign-in, CSRF, role checks, and the call to the right service |
| [src/web/templates/](src/web/templates/) | The HTML pages, one file per screen, plus a shared filter bar |
| [src/web/static/style.css](src/web/static/style.css) | The single stylesheet (no external fonts or scripts) |
| [src/persistence/lifecycle.py](src/persistence/lifecycle.py) | The status table and who may make each change |
| [src/persistence/workflow.py](src/persistence/workflow.py) | Assign, status changes, comments: each one atomic transaction |
| [src/persistence/reporting.py](src/persistence/reporting.py) | Search, filter, sort, dashboard, overdue, CSV, duplicate check |
| [src/persistence/request_service.py](src/persistence/request_service.py) | Submitting and viewing requests; combines workflow and reporting |
| [src/persistence/admin_service.py](src/persistence/admin_service.py) | Accounts, roles and categories (Administrator only) |
| [src/persistence/password_reset.py](src/persistence/password_reset.py), [user_service.py](src/persistence/user_service.py) | Single-use reset links; registration and password rules |
| [src/persistence/outbox.py](src/persistence/outbox.py) | Sends in-app and email notifications from stored events |
| [src/persistence/schema.sql](src/persistence/schema.sql), [migrations.py](src/persistence/migrations.py) | The database tables and numbered, repeatable upgrades |
| [wsgi.py](wsgi.py) | Start-up: creates the database, seeds demo accounts, starts the app |

### Proof: tests and live checks

| Where | What it is |
|---|---|
| [tests/](tests/) | 280+ automated tests, one file per area (workflow, admin, management, audit, roles, registration, layout, documentation) |
| [scripts/](scripts/) | The demo launcher, live end-to-end journeys, backup and restore drill, phone-width layout check |
| [performance/](performance/) | The NFR-001 load test and how to run it |
| [.github/workflows/](.github/workflows/) | What runs on every pull request: tests, coverage gate, Ruff, Bandit, pip-audit, secret scan, traceability |

### Documentation (`docs/`)

| Folder | What you will find |
|---|---|
| [docs/START-HERE.md](docs/START-HERE.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), [REQUIREMENTS-MAP.md](docs/REQUIREMENTS-MAP.md) | The three guides: where things are, how it is built, which code proves which requirement |
| [docs/requirements/](docs/requirements/) | Functional and non-functional requirements with acceptance criteria, scope, constraints, and the RTM |
| [docs/PED/](docs/PED/) | The Project Engineering Document, numbered sections 00 to 23, with exports |
| [docs/decisions/](docs/decisions/) | The decision log, architecture decision records, the hosting recommendation, the open lifecycle proposal |
| [docs/baseline/](docs/baseline/), [docs/change/](docs/change/) | Milestone sign-offs; formal change requests |
| [docs/release/](docs/release/) | Release summary and dated evidence folders (load, journeys, restart, restore) |
| [docs/quality/](docs/quality/) | Test inventory, role matrix, defect register, technical debt |
| [docs/risk/](docs/risk/), [docs/stakeholders/](docs/stakeholders/) | Risk and assumption registers; stakeholder and conflict registers |
| [docs/deployment/](docs/deployment/) | Staging runbook, route contract, deployment direction |
| [docs/governance/](docs/governance/), [docs/security/](docs/security/) | Working agreement, AI-usage records, GitHub governance check; secret-scan evidence |
| [docs/history/](docs/history/README.md) | One short entry per change, newest first (earlier entries: [PROJECT_HISTORY.md](PROJECT_HISTORY.md)) |

### Repository root

[PROJECT_RULES.md](PROJECT_RULES.md) (how the team works) | [requirements.txt](requirements.txt) (pinned dependencies) | [requirements-staging.txt](requirements-staging.txt) (demo extras) | [.env.example](.env.example) (setting names, no values) | [tools/](tools/) (history and AI-record helpers, PED builder)

## Run it yourself

Use only synthetic data. You need Git and Python 3.11 or later.

### The full demo in two commands

This creates an isolated local database with 14 synthetic accounts and 500 sample requests. Nothing leaves your machine and no email is sent. It needs OpenSSL (Git for Windows includes it).

```bash
git clone https://github.com/DonLukus/Civic-connect.git
cd Civic-connect
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1     Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-staging.txt
python -m scripts.m3_staging prepare     # once
python -m scripts.m3_staging serve       # then open http://127.0.0.1:5083/login
```

Logins are generated into the git-ignored `.m3-local/config.json`. Never commit that file. A good first walk-through: submit a request as a Requester, assign it as a Manager, work and resolve it as Staff, then create an account as an Administrator.

### Run the app yourself

**Windows (PowerShell):**

```powershell
python -m pip install -r requirements.txt
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:DATABASE_URL = Join-Path (Get-Location) "civicconnect-local.sqlite"
$env:SESSION_COOKIE_SECURE = "false"
$env:OUTBOX_WORKER_ENABLED = "false"
python -m flask --app wsgi:app run --host 127.0.0.1 --port 5000
```

**Linux and macOS (Bash):**

```bash
python -m pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DATABASE_URL="$PWD/civicconnect-local.sqlite"
export SESSION_COOKIE_SECURE=false
export OUTBOX_WORKER_ENABLED=false
python -m flask --app wsgi:app run --host 127.0.0.1 --port 5000
```

Open `http://127.0.0.1:5000/register` to create a synthetic Requester, then sign in at `/login`. The database is created on first start with one category, "Utilities"; an Administrator manages the rest. The application does **not** read a `.env` file (no dotenv package is installed), so set variables in your shell; [.env.example](.env.example) only lists the names. The Linux/macOS commands are not a recorded fresh walkthrough.

Privileged demo accounts can be created with the optional `BOOTSTRAP_*` variables below; day-to-day account management is done by an Administrator under Users.

### Configuration

All settings are environment variables. Keep secrets and databases out of Git.

| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Required. Signs session cookies; random and private per environment |
| `DATABASE_URL` | SQLite **file path** (default `civicconnect.sqlite`). A PostgreSQL URL is not supported |
| `SESSION_COOKIE_SECURE` | `false` for loopback HTTP; `true` when served over HTTPS |
| `PASSWORD_HASH_COST` | bcrypt cost, default 12, allowed 10 to 16 |
| `BOOTSTRAP_<ROLE>_EMAIL`, `BOOTSTRAP_<ROLE>_PASSWORD` | Optional first account for `REQUESTER`, `STAFF`, `MANAGER` or `ADMIN`; both or neither; password at most 72 bytes; existing accounts are never changed |
| `OUTBOX_WORKER_ENABLED`, `OUTBOX_WORKER_POLL_SECONDS` | `true` starts the notification loop (needs the SMTP settings); poll default 60 s |
| `APP_BASE_URL` | Public address used in password-reset emails (default `http://127.0.0.1:5000`) |
| `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD`, `EMAIL_FROM_ADDRESS` | SMTP delivery; port default 587 and STARTTLS is always used; a username needs a password |
| `FLASK_ENV` | Listed in the template only; not used by the app |

### Run the tests and checks

```bash
python -m pytest tests/ -q                                  # all automated tests
python -m pytest tests/ -q --cov=src.persistence            # with coverage (first: pip install pytest-cov)
python -m scripts.check_layout_overflow                     # phone and desktop layout (needs Chrome or Edge)
python -m scripts.m3_verify_live journeys                   # live end-to-end journeys (with the demo server running)
```

The full live procedure (load test, journeys, restart, restore) is in the [staging runbook](docs/deployment/m3-staging.md). Dependencies are pinned in [requirements.txt](requirements.txt) (Python 3.11 in CI; Gunicorn is Unix-only, the Windows demo uses Waitress).

## Security and honest limits

**What protects it:** passwords are bcrypt hashes; sessions are HttpOnly, SameSite=Lax cookies; every form carries a CSRF token; every request re-reads the user, so a deactivated account stops working at once; every role is checked on the server; user input reaches the database only as bound parameters; secrets live in environment variables; audit tables reject edits and deletes through the application.

**What is not done, stated plainly**

- **Not ready for public production.** Hosting is undecided ([DEC-008](docs/decisions/DEC-008-recommendation.md)); durable hosted storage, real external email delivery and a hosted performance run do not exist.
- **No login or password-reset rate limiting**, and existing sessions are not revoked when a password is reset.
- **Email** has only been exercised against a local test mail server.
- **The lifecycle rules** beyond what FR-014 to FR-018 state are a [proposal](docs/decisions/DEC-019-lifecycle-transition-table.md) awaiting the team.
- **The 40.00% scope result** describes the earlier slice; the newer work needs independent re-assessment.
- **Not evidenced:** availability and cold start (NFR-002), the cost review (NFR-010), 5,000-request capacity (NFR-013), usability and full accessibility (NFR-007, NFR-008).
- Someone who owns the database file could drop the audit protections.

Authoritative detail: [release summary](docs/release/m3-release-evidence-summary.md), [defect register](docs/quality/defect-register.csv), [technical debt](docs/quality/technical-debt-register.md), [risk register](docs/risk/risk-register.csv).

## Governance and contributing

Work happens on a branch and goes through a pull request with **two approvals from people other than the author**, resolved review comments and an AI-assistance declaration. Two accounts owned by one person count as one reviewer. Never push to `main`. The rules are in [PROJECT_RULES.md](PROJECT_RULES.md).

For every change: add a short history entry as a new file in [docs/history/](docs/history/README.md) and an AI record in [docs/governance/ai-usage/](docs/governance/ai-usage/README.md) (`python tools/ai_register.py --next` gives the next ID); update the RTM and any affected register; run the tests. Branch names: `feature/<FR-nnn>-<description>`, `docs/<area>`, `fix/<issue>`, `chore/<description>`, `m4/<topic>`. Commit messages: `type(scope): summary (refs identifier)`.
Branch protection on `main` requires a pull request and two approvals; the [governance check](docs/governance/github-governance-verification-2026-10-17.md) records the gaps (stale-approval dismissal off, no required status checks, bypass actors unverified).

## Team

| Member | Responsibility in this project |
|---|---|
| **Don** | Architecture, core implementation, repository and configuration |
| **Masego** | Problem, stakeholders and scope; verification and traceability |
| **Emile** | Risk and document control; staging, performance, release evidence and the PED |

All three are accountable for the whole project; authorship and review evidence are in the pull requests, [history](docs/history/README.md) and the [AI register](docs/governance/ai-usage/README.md).

## Licence

No licence has been chosen and no `LICENSE` file is committed, so all rights are reserved by default. The team, and the university if it has a claim on coursework, must decide before anyone reuses the code.
