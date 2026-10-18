# CivicConnect

Community service request management platform for SEN381, Belgium Campus ITversity, 2026.

**Team repository: [DonLukus/Civic-connect](https://github.com/DonLukus/Civic-connect).** Check `git remote -v` before using a checkout or reporting its status; similarly named repositories are not interchangeable.

## Current status

| Area | Position |
|---|---|
| M3 evaluation slice | Implemented, reviewed and merged through PR #85, including the role-matrix/RTM work from #86 |
| PED | Continuing M1/M2 document through M3 section 22; corrected full export merged through #89/#90 |
| Decisions | #88 recorded DEC-013 through DEC-018; ADR-001/007 remain Proposed and DEC-008 remains Deferred |
| Automated suite | 60 pytest cases; service, in-process web/integration and role/registration regressions, not 60 browser tests |
| Staging | Isolated local Waitress/SQLite environment with synthetic users and a local SMTP sink |
| Public production | **NOT READY** |

Status reconciled 18 October 2026 against main `af2f5456a9a940f6c9a020db5cd5fe5e4889219d` (PR #91). This README correction does not create a new release approval, milestone signature or requirement acceptance. See [PED section 22](docs/PED/22-m3-construction-verification-release.md) and the dated update in the [release evidence summary](docs/release/m3-release-evidence-summary.md).

## Purpose and implemented scope

CivicConnect aims to replace fragmented requests across email, telephone, WhatsApp, spreadsheets and paper with a controlled request record, clear ownership and attributable changes.

The merged supervised M3 slice provides:

- Public Requester registration and session-based login. Self-registration always creates a Requester.
- Requester submission with controlled categories, confirmation, own request list/detail and current status.
- Staff login, role-scoped queue, status filtering, detail and self-acceptance with version/conflict checks.
- Acceptance audit/outbox records and Requester in-app notification; SMTP transport was exercised against a local sink.
- Manager and Administrator login with safe landing pages. Operational dashboards and administration are not implemented by those pages.

The current lifecycle implements **New to Accepted**, not the entire baseline lifecycle. FR-012 supplies status filtering, not the full search/filter/sort requirement. Registration does not complete Administrator provisioning or audit under FR-001. Acceptance notification does not complete every FR-009 notification trigger.

[CHG-002](docs/change/CHG-002-m3-delivery-slice.md) records the scoped evaluation proposal; its dated pending wording is followed by the recorded decisions in PED section 22 and the release-summary update. Deferred baseline obligations remain visible and are not marked fulfilled by narrowing the demonstration. [Requirements and original acceptance criteria](docs/requirements/) and the [RTM](docs/requirements/RTM.csv) remain the controlled references.

## Runtime and data

The implementation uses Python, server-rendered Flask, SQLite, bcrypt and a transactional request/audit/outbox design. Pinned application dependencies are in [requirements.txt](requirements.txt); CI uses Python 3.11. Gunicorn is for Unix hosting and does not run on Windows. Local simulated staging uses the separate [staging requirements](requirements-staging.txt) and Waitress.

SQLite records persist in the configured local file across process restarts; that is not proof of hosted durability. No PostgreSQL implementation or final production-platform acceptance is claimed. Fresh accounts use bcrypt; successful login upgrades supported legacy hashes, but dormant legacy accounts still need an explicit migration/reset disposition.

## Run locally on Windows

Use only synthetic data. Do not expose this demonstration to real users or put credentials in Git.

Prerequisites: Git and Python 3.11 or later with pip. Open PowerShell:

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

Open `http://127.0.0.1:5000/register` to create a synthetic Requester, then sign in at `/login`. `wsgi.py` initialises the schema and default Utilities category. These commands set the environment directly: copying [.env.example](.env.example) alone does not populate the required values or guarantee a dotenv loader is installed. Keep the generated signing key stable for the local session; a new key invalidates old sessions.

Privileged demo users can be provisioned through the optional bootstrap environment variables named in `.env.example`. For the complete Staff/notification demonstration, follow the isolated [M3 staging runbook](docs/deployment/m3-staging.md), which generates synthetic fixtures and a local STARTTLS mail sink. Do not run its fixture generator against an existing database. Public HTTPS and external mail delivery require separate verification.

## Tests and evidence

```powershell
python -m pytest tests/ -q
```

The current suite contains 60 cases. The earlier 15-, 18-, 39- and 50-case reports are historical snapshots. Flask test-client cases are in-process functional/integration tests. Separate live HTTP journeys and supplementary browser walkthrough evidence are recorded; no persistent browser automation suite is claimed.

The recorded NFR-001 local warm-instance measurement used 10 Staff users, 500 filtered records and 300 seconds: 8,503 successful requests, zero failures, p95 0.422 seconds. Load/restart/backup evidence predates registration and was not silently relabelled as a rerun on later revisions. It is not hosted availability, cold-start, browser-rendering or production-capacity evidence.

- [Release evidence and residual risks](docs/release/m3-release-evidence-summary.md)
- [Test inventory](docs/quality/test-inventory.md), [role-operation matrix](docs/quality/role-operation-matrix.md) and [verification handoff](docs/quality/m3-verification-handoff.md)
- [Route/UI contract](docs/deployment/m3-interface-agreement.md)
- [Quality, secret-scan and traceability workflows](.github/workflows/)

Evaluate the exact commit and run, not only a test count or green badge. Passing CI does not establish all 40 requirements or production readiness.

## Remaining work

Public production remains NOT READY. Outstanding behaviour and assurance include:

- Full lifecycle/resolution/rejection, comments, password reset, broader search/filter/sort, Manager reporting and operational Administrator functions.
- Durable hosted storage, external SMTP/TLS, outbox recovery/idempotency, dormant legacy hashes and schema-compatible rollback.
- Sustained availability, cold-start, capacity and accessibility evidence; daily backup scheduling/retention beyond the recorded local restore drill.
- Final technology/hosting decisions and evidence-backed disposition of remaining acceptance criteria.

Use the release summary, RTM, [defect register](docs/quality/defect-register.csv) and [technical-debt register](docs/quality/technical-debt-register.md) for the authoritative details and owners. A successful scoped demonstration is not acceptance of the whole product baseline.

## Governance and contributions

Work on a branch and open a PR. Substantive changes require two approvals from different non-author people, resolved review discussions, updated affected records and an AI-assistance declaration. Two accounts owned by one person are not two independent reviewers. Follow [PROJECT_RULES.md](PROJECT_RULES.md); do not push feature changes directly to main or stage temporary review files indiscriminately.

Main has active protection rulesets requiring a PR and two approvals. The [17 October governance verification](docs/governance/github-governance-verification-2026-10-17.md) records narrower gaps: stale-approval dismissal is off and required-status-check lists are empty. Last-push approval and conversation resolution are on. Bypass actors and platform secret-scanning settings remain unverified without administrator evidence. The verification PR records discrepancies; it does not fix settings or prove every historical approval was independent.

## Project records and responsibilities

| Topic | Source |
|---|---|
| Rules, ownership and progressive history | [Project rules](PROJECT_RULES.md), [history](PROJECT_HISTORY.md) |
| Continuing PED and reproducible PDF build | [PED index](docs/PED/README.md), [full review PDF](docs/PED/exports/PED_v3.0-review.pdf) |
| Original scope and requirements | [Controlled requirements](docs/requirements/), [RTM](docs/requirements/RTM.csv) |
| Architecture and decisions | [ADRs](docs/decisions/adr/), [decision log](docs/decisions/decision-log.csv) |
| Risk and AI accountability | [Risk register](docs/risk/risk-register.csv), [AI register](docs/governance/ai-usage-register.csv) |

Current M3 responsibilities recorded in document control: Don - architecture/core/configuration; Masego - verification/traceability; Emile - staging/performance/release/PED. These describe the M3 allocation; the historical M1 ownership in PROJECT_RULES is retained. All three remain accountable for the whole project.

The full PED export includes all existing numbered sources and preserves historical signatures and dates. Section 18 has no source and remains an explicit gap. Record the actual submission date and final documentation identifier when submitting; this README supplies neither a signature nor a submission claim.
