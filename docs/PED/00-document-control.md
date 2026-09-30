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

Note on the M2 team table above: the Member A/B/C split for Milestone 2 is not the same grouping as the Workstream A/B/C split above it — those were fixed at M1 baseline and stay as the historical record. M2 uses its own lettering, matching the assessment brief's grading criteria (Emile: criteria A + B, architecture and requirements; Don: criteria C + E, data and design patterns; Masego: criteria D + F, technology and delivery).

### Authorship, review and approval

| Member | Authored | Reviewed | Approval |
|---|---|---|---|
| Masego | §2, 3, 4, 5, 10 | §6, 7, 8, 9, 11–13 | Approved 8 September 2026 |
| Don | §6, 7, 9, 12 | §2–5, 10, 11, 13 | Approved 8 September 2026 |
| Emile | §1, 8, 11, 13, 14, 15 | §2–7, 9, 10, 12 | Approved 8 September 2026 |

Every section was reviewed by two members other than its author, through pull requests. Authorship identifies who drafted a section; all three members are accountable for the whole document. The gate decision rests with the assessor.

### Linked controlled artefacts

Registers reproduced in this document are extracts taken at baseline. The CSV set in the repository is the source of truth (DEC-005).

| Artefact | Location | State at v1.0 |
|---|---|---|
| Requirements, scope, constraints | docs/requirements/ | Baselined |
| Traceability matrix | docs/requirements/RTM.csv | 40 of 40 traced |
| Risk and assumption registers | docs/risk/ | 14 risks, 5 assumptions |
| Decision log | docs/decisions/ | 10 decided, 2 deferred |
| Forward engineering register | docs/forward-engineering/ | 7 considerations |
| AI usage register, governance, sign-off | docs/governance/, docs/baseline/ | Live and controlled |
