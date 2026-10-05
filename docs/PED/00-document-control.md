# Document Control

> **PED section, v1.0 baselined, now evolving to v2.0.** Owner: Emile.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` at M1, `PED_v2.0.docx` at M2 (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

## SEN381 Software Engineering 381 — Project Engineering Document

**CivicConnect — Community Service Request Management Platform**
Version 2.0 (in progress) — Architecture, Technology & Initial Design Baseline · Milestone 2, evolving from the v1.0 Milestone 1 baseline below

| Field | Record |
|---|---|
| Module | SEN381 Software Engineering 381 (NQF 8), Belgium Campus ITversity |
| Team (M1 workstreams) | Masego (Workstream A) · Don (Workstream B) · Emile (Workstream C) |
| Team (M2 members) | Emile (Member A) · Don (Member B) · Masego (Member C) — see note below, the lettering changes between milestones |
| Repository | https://github.com/DonLukus/Civic-connect |
| Baseline date | M1: 8 September 2026 · M2: in progress |
| Governing document | SEN381 CivicConnect Master Project Brief v1.1 (2026); SEN381 CivicConnect Milestone 2 brief |
| Status | M1 baselined and gated. M2 underway: architecture, data, technology and design decisions not yet finalised. |

## Document Control

| Ver | Date | Author | Change | Reviewed by | Status |
|---|---|---|---|---|---|
| 0.1 | 2026-09-08 | Masego | Problem, stakeholders, scope, constraints, decisions | Don, Emile | Draft |
| 0.2 | 2026-09-08 | Don | Requirements, acceptance criteria, RTM, forward engineering, repository governance | Masego, Emile | Draft |
| 0.3 | 2026-09-08 | Emile | Risk, AI control, working agreement, document control | Masego, Don | Draft |
| 0.9 | 2026-09-08 | Emile | Sections integrated; identifiers reconciled across all registers | Masego, Don | In review |
| 1.0 | 8 September 2026 | Team | Baselined. Scope, requirements and acceptance criteria under change control. | All three | BASELINED |
| 2.0 (in progress) | 2026-09-30 | Emile | M2 document control opened. PED continues from the v1.0 baseline — nothing below is rewritten, M2 adds new sections (16–21) for architecture, data, technology, design and the M2 sign-off. | Don, Masego (pending) | Draft |
| 2.0 review candidate | 2026-10-01 | Emile | Reconciled PoC, campus test, PR #62 and Render deployment evidence with the architecture and deployment sections. | Don, Masego (pending) | In review |

Note on the M2 team table above: the Member A/B/C split for Milestone 2 is not the same grouping as the Workstream A/B/C split above it — those were fixed at M1 baseline and stay as the historical record. M2 uses its own lettering, matching the assessment brief's grading criteria (Emile: criteria A + B, architecture and requirements; Don: criteria C + E, data and design patterns; Masego: criteria D + F, technology and delivery).

### Authorship, review and approval

| Member | Authored | Reviewed | Approval |
|---|---|---|---|
| Masego | §2, 3, 4, 5, 10 | §6, 7, 8, 9, 11–13 | Approved 8 September 2026 |
| Don | §6, 7, 9, 12 | §2–5, 10, 11, 13 | Approved 8 September 2026 |
| Emile | §1, 8, 11, 13, 14, 15 | §2–7, 9, 10, 12 | Approved 8 September 2026 |

Every section was reviewed by two members other than its author, through pull requests. Authorship identifies who drafted a section; all three members are accountable for the whole document. The gate decision rests with the assessor.

### Linked controlled artefacts

Registers reproduced in this document are extracts taken at baseline. The CSV set in the repository is the source of truth (DEC-005). The "State at M2 (in progress)" column is added here, not substituted for the v1.0 column, per the same never-overwrite rule that governs the rest of this document.

| Artefact | Location | State at v1.0 | State at M2 (in progress) |
|---|---|---|---|
| Requirements, scope, constraints | docs/requirements/ | Baselined | Unchanged except CHG-001 (§10.3) |
| Traceability matrix | docs/requirements/RTM.csv | 40 of 40 traced | M2 columns added; 3 of 40 rows carry real M2 evidence, the rest read Pending M2 — tracked on Issue #66 |
| Risk and assumption registers | docs/risk/ | 14 risks, 5 assumptions | 16 risks (RSK-15, RSK-16 added) |
| Decision log | docs/decisions/ | 10 decided, 2 deferred | **Gap:** 6 new ADRs exist in docs/decisions/adr/ (ADR-001, 002, 003, 004, 006, 007) but none has a corresponding DEC- row yet in docs/decisions/decision-log.csv or this document's §10 table — tracked on Issue #65 |
| ADR set | docs/decisions/adr/ | Did not exist | 6 ADRs: Accepted — ADR-002, 003, 004, 006; Proposed — ADR-001, ADR-007 |
| Forward engineering register | docs/forward-engineering/ | 7 considerations | Unchanged |
| AI usage register, governance, sign-off | docs/governance/, docs/baseline/ | Live and controlled | M2 baseline sign-off recorded in docs/baseline/M2-baseline-signoff.md — see §21 and the graduation checklist below |

## When v2.0 moves from Draft to BASELINED

This document does not assert v2.0 is baselined — it stays Draft/In review until every item below is objectively true, verified against the actual controlled artefact named, not asserted here. This mirrors exactly how v1.0 graduated: a final `BASELINED` row gets appended below the current "2.0 review candidate" row (never edited in place — the draft history stays visible), once:

| # | Condition | Verified against |
|---|---|---|
| 1 | ADR-001 status is Accepted, not Proposed | `docs/decisions/adr/ADR-001-architecture-and-stack-options.md` |
| 2 | ADR-007 status is Accepted, not Proposed | `docs/decisions/adr/ADR-007-authentication-authorization-placement.md` |
| 3 | DEC-008's evidence (login/save/deploy on a live host, verified not assumed) exists | `docs/decisions/poc-log.md` |
| 4 | Every M2 ADR has a corresponding DEC- row | `docs/decisions/decision-log.csv` + §10 |
| 5 | §18 (technology stack narrative) exists | `docs/PED/18-technology-stack.md` — outstanding, Masego (Issue #65/#66 overlap) |
| 6 | RTM M2 columns are populated for all 40 rows, not just the traced slice (implementation evidence may still legitimately read Pending for unbuilt requirements — architecture/data/design/technology links may not) | `docs/requirements/RTM.csv` — Issue #66 |
| 7 | `docs/baseline/M2-baseline-signoff.md`'s own Outcome field reads ACCEPTED, signed by all three | that file directly |

Once all seven hold, the final Document Control row and this section both get a follow-up PR updating "Status" (row above) and the Baseline date field to the real M2 date — not before.
