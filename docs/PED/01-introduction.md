# Introduction

> **PED v1.0 section.** Owner: Emile.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

This is the single evolving engineering record for CivicConnect [1, §6]. Version 1.0 establishes the baseline: what the team commits to build, for whom, within what constraints, what it has deliberately not decided, and how change will be controlled. It is extended, not replaced, at each milestone — v2.0 adds architecture and design, v3.0 construction and quality evidence, v4.0 the final success evaluation.

M1 is a foundation milestone. Technology stack, architecture, database schema, UI, API contracts, CI pipeline and deployment are outside its boundary. Section 14 records what is deferred and why.

## 1.1 Identifier scheme

Stable identifiers make traceability possible across four milestones (DEC-003). They are never reused or renumbered after baseline, because every later artefact attaches to them.

| Prefix | Artefact | Prefix | Artefact |
|---|---|---|---|
| SH-nn | Stakeholder | RSK-nn | Risk |
| CF-nn | Stakeholder conflict | AS-nn | Assumption |
| SCOPE-I/O/D-nn | Scope: in, out, deferred | DEC-nnn | Engineering decision |
| CN-nn | Constraint | FEC-nn | Forward engineering consideration |
| FR-nnn / NFR-nnn | Requirement | AI-nnn | AI usage entry |
| AC-nnn / AC-Nnnn | Acceptance criterion | CHG / TST / DEF-nnn | Change, test, defect (reserved) |
| TR-nnn | Traceability record | | |

## 1.2 References

| Ref | Source | Used for |
|---|---|---|
| [1] | SEN381 CivicConnect Master Project Brief v1.1 (2026) | Project-wide controls; scenario; minimum business capabilities |
| [2] | SEN381 Milestone 1 Brief (2026) | Required M1 outputs and the milestone gate |
| [3] | ISO/IEC/IEEE 29148:2018 — Requirements engineering | Requirement quality attributes applied in §6 |
| [4] | ISO/IEC 25010:2011 — System and software quality models | Quality attribute categories structuring the NFRs |
| [5] | PMBOK Guide, 7th ed. (PMI, 2021) | Probability × impact risk scoring in §8 |
| [6] | W3C WCAG 2.1 Level AA | Accessibility criteria in NFR-008 |

Citations support why a practice is appropriate; they are not evidence that a control was implemented. Implementation claims rest on repository history, register entries and configuration evidence [2, §9.1].

---

## References (compiled §16 — full bibliography)

- Belgium Campus ITversity, 2026. *SEN381 CivicConnect Master Project Brief*, Version 1.1.
- Belgium Campus ITversity, 2026. *SEN381 Milestone 1 Brief: Engineering Foundation & Requirements Baseline*.
- International Organization for Standardization, 2018. *ISO/IEC/IEEE 29148:2018 Systems and software engineering — Life cycle processes — Requirements engineering*. Geneva: ISO.
- International Organization for Standardization, 2011. *ISO/IEC 25010:2011 Systems and software engineering — SQuaRE — System and software quality models*. Geneva: ISO.
- Project Management Institute, 2021. *A Guide to the Project Management Body of Knowledge (PMBOK Guide)*, 7th ed. Newtown Square, PA: PMI.
- World Wide Web Consortium, 2018. *Web Content Accessibility Guidelines (WCAG) 2.1*. W3C Recommendation.

> Before submitting: confirm this list matches the required referencing style and that every citation marker resolves to an entry. Missing in-text citations and references result in an automatic mark of zero [2, §10]. Verify each source independently and add any others the team actually consulted.
