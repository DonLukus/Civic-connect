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

### 2026-09-30 — M2 bootstrap: PR template, branch rule, env template, versions, deployment direction
**Who:** Masego · **Type:** governance, artefact
**What:** Closed the Days 1-5 M2 checklist gaps found on audit. Added a "How this was tested"
field to the PR template; documented the `m2/<topic>` and `feature/<FR-nnn>-<desc>` branch
conventions in `PROJECT_RULES.md` §9; added `.env.example` (names only); pinned and verified
Flask 3.1.3 (BSD-3-Clause) and pytest 9.1.1 (MIT) against PyPI's published metadata, recorded in
`docs/decisions/technology-versions.md`; drafted `docs/deployment/deployment-direction.md`
(Proposed, same gate as ADR-001); added RSK-15 for dependency-version drift on the untested lab
platform.
**Affects:** `.github/pull_request_template.md`, `PROJECT_RULES.md` §9, `.env.example`,
`requirements.txt`, RSK-15.
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
