# Project History

Running record of every significant change, decision and milestone event on CivicConnect.

**Purpose.** The PED states what is *true* about the project. This file states what *happened* — in
date order, with who and why. Together with `PROJECT_RULES.md` they are the files any team member or
AI assistant reads to get up to speed without asking anyone.

**Rule.** Every pull request adds an entry here. Newest at the top.

---

## Format

```
### YYYY-MM-DD — Short title
**Who:** name · **Type:** decision | artefact | governance | risk | change | milestone
**What:** one or two sentences.
**Affects:** identifiers and artefacts touched.
**Evidence:** PR #, commit, or artefact path.
```

---

### 2026-09-30 — M2 deployment PoC: wsgi.py and gunicorn added, Render deployment left explicit
**Who:** Masego · **Type:** artefact, decision
**What:** Built the production entrypoint (`wsgi.py`) for DEC-008's proof-of-concept requirement.
Checked first that neither `RequestService` nor `RequestRepository` initialises the database
schema (they don't), so `wsgi.py` does it once, idempotently — verified by importing it twice
against the same file in separate processes and confirming no error and no duplicate rows.
Added and verified `gunicorn==26.2.0` (MIT, PyPI-checked). Confirmed by actually installing it in
an isolated venv that gunicorn cannot run on Windows (`fcntl` is Unix-only) — expected, since it
only needs to run on Render, but confirmed rather than assumed. Full existing test suite still
10/10 passing. **Did not** perform the actual Render deployment, the idle-timeout persistence
observation, or the Belgium Campus lab-machine check — none possible from this session (no Render
account/API access; no access to confirm this dev machine matches the institutional platform).
`docs/decisions/poc-log.md` states each gap explicitly with exact next steps for whoever has that
access, rather than guessing at a result. Does not move ADR-001 or DEC-008's status — that is a
team decision once the real evidence exists.
**Affects:** `wsgi.py` (new), `requirements.txt`, `docs/decisions/technology-versions.md`,
`docs/decisions/poc-log.md` (new). DEC-008 and ADR-001 status unchanged, deliberately.
**Evidence:** Issue #52; branch `m2/poc-deployment`; 10/10 tests passing; AI-023.

### 2026-09-30 — README rewritten in plain, grade-8-level English
**Who:** Masego · **Type:** artefact
**What:** Rewrote `README.md` for accessibility — shorter sentences, plain words, jargon
explained on first use. Also refreshed facts that had gone stale: test count (7 → 10), ADR count
and status (6 files, 4 Accepted / 2 Proposed), risk count (16), and the "where the design patterns
appear" section, which still described ADR-003's transition-table validator as un-extracted after
it had already been moved into `src/persistence/lifecycle.py`.
**Affects:** `README.md`.
**Evidence:** Issue #50; branch `docs/readme-plain-language`; AI-022.

### 2026-09-30 — ADR-007 proposed: authentication/authorization placement (resolves RSK-16's design gap)
**Who:** Masego · **Type:** decision
**What:** Drafted ADR-007 following Emile's RSK-16 finding on ADR-001 review. Decision: identity
via Flask's built-in session at the route layer; authorization checked inside the domain service,
per-record, before any write — the same placement ADR-002's transaction and ADR-003's transition
guard already use, not a route decorator (which cannot express NFR-012's per-record "assigned
staff member only" rule). Placement only — FR-001..FR-004 (the login feature itself) is not built
here. Updated RTM `TR-015` (NFR-012) and `TR-017` (NFR-004) to "Design decided, implementation
pending" rather than leaving them at Pending M2 with no design behind that status. Also advanced
`TR-007` (FR-025), `TR-008` (NFR-006) and `TR-011` (FR-014) to reflect the audit-trail and
lifecycle-validator evidence that already exists in `src/persistence/`.
**Affects:** ADR-007 (new); RSK-16 (moves from "undecided" to "placement decided, not
implemented"); TR-007, TR-008, TR-011, TR-015, TR-017.
**Evidence:** Issue #46; branch `m2/auth-placement-adr`; 10/10 tests still passing (no code
behaviour changed, RTM and ADR only).

### 2026-09-30 — M2 brief compliance pass: diagram, baseline sign-off, PED fix, ADR-003 evidence
**Who:** Masego · **Type:** artefact, decision, governance
**What:** Checked the repo against the actual M2 brief text for the first time (previously
working from context alone) and closed four gaps. Added the M2 brief's required architecture
diagram (mermaid, logical layers vs. physical deployment) to ADR-001. Wrote the missing
Architecture/Technology/Initial Design Baseline sign-off - status Proposed, honestly listing what
remains open. Fixed a real defect: `docs/PED/17-data-persistence.md`, `19-design-decisions.md`
and `20-integration-deployment.md` each held a different section's content than their filename
claimed, and one of them was actually `ADR-006: Integration Decision` mis-filed as a PED section
- rotated to the correct files and extracted ADR-006 properly. Extracted ADR-003's New->Accepted
guard out of `RequestService.accept_request` into `LifecycleValidator`, tested directly - closing
the "documented decision, no extracted implementation" gap, deliberately without inventing the
rest of FR-015's transition table, which has no approved specification yet. Also resolved merge
conflicts (additive, not substantive) between four separately-authored open PRs and `main` -
`ai-usage-register.csv`, `RTM.csv`, `risk-register.csv`, `PROJECT_HISTORY.md` - each time because
two branches appended non-overlapping rows/entries at the same point.
**Affects:** ADR-001, ADR-003, ADR-006 (new), TR-012, `docs/baseline/M2-baseline-signoff.md`
(new), `docs/PED/17`/`19`/`20`, `src/persistence/lifecycle.py` (new).
**Evidence:** Issue #44; branch `m2/architecture-diagram-and-baseline`; 10/10 tests passing.

### 2026-09-30 — Traced slice built: citizen submits a service request (FR-005, FR-006)
**Who:** Masego · **Type:** artefact
**What:** Built the M2 traced slice end to end per ADR-001: `RequestService.create_request`
(mandatory-field and active-category validation, request + audit rows in one transaction, no
outbox row since FR-009 doesn't trigger on submission), a server-rendered Flask form
(`src/web/`), and 6 passing tests covering the service and the full web route. Added a
`test.yml` GitHub Actions workflow so the suite runs on every PR. Filled the RTM M2 columns for
TR-001/TR-013 with real implementation and verification evidence. Rewrote the README for the
actual M2 state and verified its setup steps by running them, not just writing them.
**Found and fixed while building this:** `with sqlite3.connect(...) as conn:` commits/rolls back
on exit but does not close the connection (stdlib behaviour) - left open, this held a Windows
file lock that made the *existing* acceptance-path test (`test_request_acceptance.py`, believed
passing) fail on Windows. Fixed with explicit `try/finally: conn.close()` throughout
`src/persistence/` and both test files - concrete evidence for RSK-03/RSK-15, not hypothetical.
**Affects:** FR-005, FR-006, TR-001, TR-013, ADR-001; `src/web/`, `src/persistence/request_service.py`, `tests/`, `.github/workflows/test.yml`, `README.md`.
**Evidence:** Issue #34; branch `feature/FR-005-submit-request`; 7/7 tests passing (`python -m pytest tests/ -v`).

### 2026-09-30 — M2 bootstrap: PR template, branch rule, env template, versions, deployment direction
**Who:** Masego · **Type:** governance, artefact
**What:** Closed the Days 1-5 M2 checklist gaps found on audit. Added a "How this was tested"
field to the PR template; documented the `m2/<topic>` and `feature/<FR-nnn>-<desc>` branch
conventions in `PROJECT_RULES.md` §9; added `.env.example` (names only); pinned and verified
Flask 3.1.3 (BSD-3-Clause) and pytest 9.1.1 (MIT) against PyPI's published metadata, recorded in
`docs/decisions/technology-versions.md`; drafted `docs/deployment/deployment-direction.md`
(Proposed, same gate as ADR-001); added RSK-15 for dependency-version drift on the untested lab
platform. Also fixed an unrelated CI failure surfaced while merging: `secret-scan.yml` had CRLF
line endings and a fragile embedded-quote regex that broke bash parsing on the Actions runner
specifically - normalized to LF, simplified the pattern, added `.gitattributes` so it can't
recur.
**Affects:** `.github/pull_request_template.md`, `PROJECT_RULES.md` §9, `.env.example`,
`requirements.txt`, RSK-15, `.github/workflows/secret-scan.yml`, `.gitattributes`.
**Evidence:** Issue #32; branch `m2/bootstrap-governance`.

### 2026-09-30 — ADR-001 proposed: architecture style, traced feature slice, stack options
**Who:** Masego · **Type:** decision
**What:** Reviewed the M1 baseline and the M2 work merged so far (ADR-002 persistence, ADR-003
lifecycle validator, ADR-004 notification fan-out, the accept-path PoC) and drafted ADR-001,
status Proposed. Recommends "Citizen submits a service request" (FR-005, FR-006) as the one
feature slice traced end to end for M2, and lists frontend/backend/database/testing/CI stack
options evaluated against the architecture already accepted, with a recommended direction per
layer. Not Accepted — still gated on the DEC-008 proof-of-concept on the real platform, and on
Don and Emile's review.
**Affects:** ADR-001; references ADR-002, ADR-003, ADR-004, DEC-008, FR-005, FR-006, FR-009,
FR-025, CN-01..CN-08.
**Evidence:** Issue #30; branch `m2/architecture-stack-options`; AI-017.

### 2026-09-09 — Workstream A verification pass: problem, stakeholders, scope, constraints, decisions
**Who:** Masego · **Type:** artefact
**What:** Verified PED §2, §3, §4, §5 and §10 against the Master Project Brief and reconciled
the registers with the PED narrative. Corrections: PED §2 symptom 2 reworded to "limited
visibility of status"; SH-05 interest re-rated Medium→High with strategy and §3 narrative
updated; SCOPE-D-03 rationale rewritten to name the evidence that unblocks it; CN-03's register
implication expanded to carry the full cost→quality→architecture→verification→evaluation chain;
DEC-007 risk link corrected to RSK-08, RSK-02. Every stakeholder confirmed to trace to ≥1
requirement; both deferred decisions confirmed to name specific evidence required.
**Affects:** SH-05, SCOPE-D-03, CN-03, DEC-007; PED §2, §3, §4, §5.1, §10.1.
**Evidence:** Issues #11–#15; branch `docs/scope-and-stakeholders`.

### 2026-09-08 — PED v1.0 baselined at the M1 engineering gate
**Who:** Team · **Type:** milestone
**What:** Scope, requirements and acceptance criteria placed under change control. Team sign-off
completed with four known limitations recorded rather than claiming completeness.
**Affects:** All M1 artefacts. Changes to baselined content now require a change request.
**Evidence:** `docs/baseline/M1-baseline-signoff.md`, PED §15.

### 2026-09-08 — Sections integrated and identifiers reconciled
**Who:** Emile · **Type:** artefact
**What:** Three workstreams merged into one coherent document. Every identifier cross-checked
against its register; a workflow now catches this automatically.
**Affects:** Whole PED, all registers.
**Evidence:** PED v0.9 → v1.0, `.github/workflows/docs-check.yml`.

### 2026-09-08 — Risk register, working agreement and AI control completed
**Who:** Emile · **Type:** risk, governance
**What:** 14 risks scored and owned; 5 assumptions linked to risks; working agreement agreed; AI
usage register established with verification recorded per entry.
**Affects:** RSK-01..RSK-14, AS-01..AS-05, AI-001..AI-006.
**Evidence:** `docs/risk/`, `docs/governance/`.

### 2026-09-08 — RSK-04 added by the team after reviewing the AI-drafted register
**Who:** Emile · **Type:** risk
**What:** The generated register missed the deadlock created by requiring two approvals in a
three-person team — a single absence blocks every merge. Added by the team and mitigated through the
24-hour review turnaround in DEC-010 rather than by weakening the control.
**Affects:** RSK-04, DEC-010, CN-08.
**Evidence:** AI-004 register entry; `docs/governance/team-working-agreement.md`.

### 2026-09-08 — Requirements, acceptance criteria and RTM completed
**Who:** Don · **Type:** artefact
**What:** 26 functional and 14 non-functional requirements baselined, each with a source, a MoSCoW
priority and acceptance criteria. All 40 traced in the RTM with columns reserved for M2–M4 evidence.
**Affects:** FR-001..FR-026, NFR-001..NFR-014, TR-001..TR-040.
**Evidence:** `docs/requirements/`.

### 2026-09-08 — Nine NFRs rewritten for measurability
**Who:** Don · **Type:** artefact
**What:** Initial drafts used unmeasurable language — "fast", "user-friendly", "secure". Each was
rewritten with a number and a verification method. A second AI model was used to attack the
acceptance criteria and found NFR-001 stated no concurrency and no data volume.
**Affects:** NFR-001, 002, 007, 008, 009, 010, 011, 013, 014.
**Evidence:** AI-002 and AI-003 register entries.

### 2026-09-08 — AI-proposed automatic triage rejected
**Who:** Don · **Type:** decision
**What:** A generated requirement set proposed AI-based classification and prioritisation of
requests. Rejected: no stakeholder need, no definable acceptance criterion, and it would place an
unverifiable component on the accountability path the project exists to establish.
**Affects:** SCOPE-O-07. Deterministic duplicate detection (FR-026) retained instead.
**Evidence:** AI-002 register entry; PED §4.4.

### 2026-09-08 — Repository governance established and verified
**Who:** Don · **Type:** governance
**What:** Protected main, pull requests required, two approvals from non-authors, stale approvals
dismissed, conversation resolution required, administrator bypass disabled, force push and deletion
blocked, secret scanning active. Verified by attempting a direct push and a self-approval — both
refused.
**Affects:** CN-08, DEC-001, NFR-005.
**Evidence:** Repository settings; refused push; `PROJECT_RULES.md` §10.

### 2026-09-08 — Repository created
**Who:** Don · **Type:** milestone
**What:** Controlled team repository initialised with the documentation structure, issue and pull
request templates, `.gitignore` covering environment and key files before any code exists, and the
secret-scanning and traceability workflows.
**Affects:** Whole project.
**Evidence:** Initial commits.

### 2026-09-08 — Problem, stakeholder, scope and constraint baseline completed
**Who:** Masego · **Type:** artefact
**What:** Nine stakeholders with five genuine conflicts, each naming the artefact that resolves it.
Scope split into 12 in-scope areas, 9 exclusions and 6 deferments. Eight constraints analysed for
engineering implications rather than merely listed.
**Affects:** SH-01..SH-09, CF-01..CF-05, SCOPE-I/O/D, CN-01..CN-08.
**Evidence:** `docs/stakeholders/`, `docs/requirements/scope-baseline.csv`.

### 2026-09-08 — DEC-008 deferred: technology stack, architecture and platform
**Who:** Team · **Type:** decision
**What:** Deliberately not decided in M1. Four pieces of evidence are missing: verified
compatibility on the Belgium Campus desktop platform, measured free-tier cold-start behaviour, an
honest capability audit, and a proof of concept covering authentication, persistence and deployment.
**Affects:** DEC-008; blocks construction, compressing M2 (RSK-12). Accepted deliberately.
**Evidence:** Decision log; PED §10.1.

---

## Template for your next entry

```
### 2026-__-__ — 
**Who:**  · **Type:** 
**What:** 
**Affects:** 
**Evidence:** 
```

## What to log

Log it if it changes what is true about the project: a decision taken or deferred; a requirement
added, changed or removed; a risk raised, re-scored or realised; a change request; a governance
control altered; a milestone gate outcome; an AI contribution that was rejected or materially
changed. Do not log typo fixes or work-in-progress commits. This is a record of consequence, not an
activity feed.
