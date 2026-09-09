# Baseline Sign-Off

> **PED v1.0 section.** Owner: Emile.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

| Field | Record |
|---|---|
| Project / baseline type | CivicConnect — engineering foundation and requirements baseline |
| Version and date | PED v1.0, 8 September 2026 |
| Scope reviewed | YES — 12 in-scope areas, 9 exclusions, 6 deferments reviewed by all three; SCOPE-O-07 defended in §4.4 |
| Requirements and traceability checked | YES — 40 requirements, all traced; each has source, priority and acceptance criteria; identifiers reconciled across all registers |
| Risk review completed | YES — 14 risks scored and owned (1 Critical, 11 High, 2 Medium); 5 assumptions linked to risks |
| Repository and governance checked | YES — protected main verified by a refused direct push and refused self-approval; two-approval rule evidenced on merged pull requests; secret scanning active |
| Outcome | ACCEPTED by the team as a sufficiently controlled foundation. The formal gate decision rests with the assessor. |

## 15.1 Known limitations

Recorded deliberately — honesty about limitations is valued above unsupported claims of completeness [1, §23].

1. No live CivicConnect stakeholder exists; the team acts as proxy (AS-01, RSK-10). Requirements are testable, but their business validity is not independently confirmed.
2. Target resolution times underlying FR-021 are provisional (RSK-05). The requirement is testable at boundary values; the values are not authorised.
3. Every NFR states a metric and a verification method, but none has been measured. They are commitments, not evidence, until M3.
4. Task-level scheduling and effort estimation follow the M2 architecture decision.

## 15.2 Declaration

We confirm this document reflects the actual engineering work of the registered team; that AI assistance is recorded with the verification applied; that each of us reviewed the whole document, not only our own workstream; and that each of us can independently locate, explain and defend any artefact in this baseline.

| Member | Workstream | Signature | Date |
|---|---|---|---|
| Masego | A | | 8 September 2026 |
| Don | B | | 8 September 2026 |
| Emile | C | | 8 September 2026 |
