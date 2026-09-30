# Forward Engineering Considerations

> **PED v1.0 section.** Owner: Don.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

Seven later lifecycle concerns that already influence current requirements, constraints, risks or assumptions [2, §4]. None is decided here — the register preserves later options rather than closing them.

### FEC-01 — Deployment environment and free-tier operating characteristics

| | |
|---|---|
| Why now | The cost constraint permits only free-tier hosting, whose idle-shutdown and capacity behaviour directly determines whether NFR-001 and NFR-002 are achievable. These NFRs are being baselined now, so the constraint shapes requirements before any deployment work begins. |
| Influences | M2 platform and architecture decision (DEC-008); M3 staging deployment; M4 operational cost review. |
| Missing information | Measured cold-start latency of candidate hosts; free-tier compute, storage and row limits; whether the platform is reachable and supported from the Belgium Campus desktop environment. |
| Risk of ignoring | Performance and availability targets are baselined that the eventual platform cannot meet, forcing either a requirements change after baseline or an undefended quality claim. |
| Links | RSK-02, RSK-03, CN-03, CN-07 |

### FEC-02 — Testability of the request lifecycle

| | |
|---|---|
| Why now | FR-015 defines a state machine and FR-025 an immutable audit trail. Both are only cheaply testable if the transition logic is separable from the user interface. That is an M2 design constraint which must be recorded now, while the requirements are being written, rather than discovered during M3 test design. |
| Influences | M2 component and layering decisions; M3 test strategy and coverage target in NFR-009. |
| Missing information | Which transitions are permitted from each terminal state, particularly whether Closed may be reopened and by whom; whether the audit trail is written by the application or enforced at the persistence layer. |
| Risk of ignoring | Transition logic embedded in controllers or pages forces slow end-to-end tests for behaviour that unit tests should cover, making NFR-009 unaffordable and regression testing unreliable. |
| Links | FR-015, FR-025, NFR-006, NFR-009 |

### FEC-03 — Automated build, integration and quality gates

| | |
|---|---|
| Why now | M3 requires automated build, test, static analysis and dependency checking. The quality gate defines what evidence must exist before a merge, so the definition of done and the acceptance criteria written now must be expressible as automated checks. |
| Influences | M2 technology choice, which determines available tooling; M3 pipeline implementation and quality-gate definition. |
| Missing information | Which build and test tooling the chosen stack supports; free-tier pipeline minute limits; whether a coverage gate can be enforced on the branch protection rule. |
| Risk of ignoring | Acceptance criteria are written that can only be verified manually, so quality evidence in M3 becomes screenshots and assertion rather than measurement. |
| Links | NFR-009, NFR-005, CN-04, DEC-008 |

### FEC-04 — Security architecture, secrets and dependency exposure

| | |
|---|---|
| Why now | Security requirements baselined in M1 (NFR-003 to NFR-006, NFR-012, NFR-014) constrain the M2 architecture. Secret handling and dependency vulnerability exposure begin the moment the first line of code exists, which is why the secret-scanning control is being enabled before construction rather than after. |
| Influences | M2 authentication, authorisation and trust-boundary design; M3 dependency scanning, security testing and configuration management. |
| Missing information | Where the trust boundaries actually sit once the architecture is known; which vulnerability-scanning tooling is available at zero cost; how configuration is injected per environment on the chosen platform. |
| Risk of ignoring | Security becomes a late hardening pass, which the Master Project Brief explicitly rejects, and a leaked credential in early history is expensive to purge and impossible to hide. |
| Links | RSK-06, RSK-11, NFR-005, CN-05 |

### FEC-05 — Data model evolution, migration and recovery

| | |
|---|---|
| Why now | The audit trail (FR-025) and the deferred legacy import (SCOPE-D-05) both constrain the persistence design. NFR-011 commits the team to a verified restore. Recovery cannot be retrofitted onto a schema that has no backup path within its free tier. |
| Influences | M2 persistence design; M3 migration approach and restore rehearsal; M4 operational readiness evidence. |
| Missing information | Free-tier backup and point-in-time-recovery capability of candidate databases; the quality and structure of the legacy spreadsheet and paper records; whether audit records are retained indefinitely or aged out under NFR-013 capacity limits. |
| Risk of ignoring | A schema is baselined that cannot support an append-only audit trail within free-tier row limits, or a restore that has never been rehearsed fails at the moment it is needed. |
| Links | NFR-011, NFR-013, FR-025, SCOPE-D-05 |

### FEC-06 — Observability and operational readiness

| | |
|---|---|
| Why now | M4 asks how the team would know the system is degrading before users complain. Logging and health checks must be designed in M2, not added in M4, and NFR-002 cannot be evidenced at all without an uptime measurement that has to be running throughout M3. |
| Influences | M2 logging and health-check design; M3 staging monitoring; M4 operational readiness and incident response evidence. |
| Missing information | What monitoring the chosen platform provides at zero cost; what log retention the free tier permits; what constitutes a meaningful health check for this application. |
| Risk of ignoring | NFR-002 has no evidence because nothing was measuring availability during the period it describes, and the M4 operational readiness claim is unsupported. |
| Links | NFR-002, NFR-011, CN-03 |

### FEC-07 — Maintainability, technical debt and knowledge transfer

| | |
|---|---|
| Why now | Only three engineers exist and each currently owns a distinct workstream. Debt incurred under M3 schedule pressure will be defended in M4, and a decision taken now to skip a control is a debt item whether or not it is recorded as one. |
| Influences | M2 design for changeability; M3 technical-debt register and rework decisions; M4 decision-consequence reflection. |
| Missing information | Which parts of the system are most likely to change for a new stakeholder need; what the team's actual review capacity is once construction begins alongside other modules. |
| Risk of ignoring | Debt accumulates unrecorded, so the M4 reflection becomes hindsight narrative rather than evidence, and single-point knowledge concentration (RSK-13) is discovered only when a member is unavailable. |
| Links | RSK-13, RSK-09, NFR-009, CN-06 |
