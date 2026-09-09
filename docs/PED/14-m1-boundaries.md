# M1 Boundaries

> **PED v1.0 section.** Owner: Emile.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

| Not decided | Why | When | Prepared |
|---|---|---|---|
| Technology stack | Requires compatibility verification, measured free-tier behaviour, a capability audit and a proof of concept — none exist yet (DEC-008) | M2 | NFRs act as selection criteria; CN-06, CN-07; RSK-03 owned |
| Architecture | Follows from architecturally significant requirements, baselined here | M2 | NFR-001, 002, 009, 013 identified as likely drivers |
| Database schema | Depends on the persistence decision; must hold an append-only audit trail within free-tier limits | M2 | FEC-05; FR-025, NFR-006 constrain the design |
| UI design | Outside the M1 boundary; targets set first so design has criteria to meet | M2 | NFR-007, NFR-008 |
| API contracts | Depend on the architecture decision | M2 | FEC-02 records the testability constraint |
| CI pipeline | Cannot be built before the stack is chosen | M3 | FEC-03; NFR-005 secret scanning already active |
| Attachments | Storage cost, malware handling and retention unknown until the platform is chosen (DEC-007) | M2 | SCOPE-D-01 with evidence required stated |
| SLA thresholds | No stakeholder authority exists to set service-level values (RSK-05) | M2 | FR-021 configurable, so it stays testable |
