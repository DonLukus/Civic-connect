# Scope Baseline

> **PED v1.0 section.** Owner: Masego.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

Baselined at v1.0; after baseline, scope changes only through a change request with impact analysis (§11.2). Excluded and deferred are separated deliberately — "we decided against this" and "we do not yet have evidence to decide" are different engineering statements.

## 4.1 In scope

| ID | Capability committed | Requirements |
|---|---|---|
| SCOPE-I-01 | Authentication and role-based access control for four roles: Requester, Staff, Manager, Administrator | FR-001..FR-004, NFR-003, NFR-004 |
| SCOPE-I-02 | Service request submission with a mandatory controlled category | FR-005, FR-006 |
| SCOPE-I-03 | Requester visibility: current status and full history of own requests | FR-007, FR-008 |
| SCOPE-I-04 | In-app and email notification on accept, reject, update and completion | FR-009 |
| SCOPE-I-05 | Staff work queue with search, filter and sort | FR-011, FR-012, FR-013 |
| SCOPE-I-06 | Assignment, self-assignment and reassignment of requests | FR-014 |
| SCOPE-I-07 | Controlled status lifecycle enforced as a state machine | FR-015, FR-017, FR-018 |
| SCOPE-I-08 | Action, comment and resolution recording on a request | FR-010, FR-016 |
| SCOPE-I-09 | Management dashboard covering open, in progress, overdue, resolved and closed work | FR-019, FR-021 |
| SCOPE-I-10 | Breakdown of activity by category, status, assignee and period, with CSV export | FR-020, FR-022 |
| SCOPE-I-11 | Administration of the controlled category list and of users and roles | FR-023, FR-024 |
| SCOPE-I-12 | Immutable audit trail of status and assignment changes | FR-025, NFR-006 |

## 4.2 Out of scope

| ID | Excluded | Rationale |
|---|---|---|
| SCOPE-O-01 | Native mobile applications (iOS / Android) | Responsive web delivery satisfies SH-01 access needs at a fraction of the build, test and release cost. Two additional deployment targets cannot be verified within the schedule. |
| SCOPE-O-02 | WhatsApp, SMS or telephone channel integration | The fragmented-channel problem is solved by consolidating onto one controlled record, not by adding further channels. Paid gateways also breach CN-03. |
| SCOPE-O-03 | Integration with existing finance, ERP, HR or asset-management systems | No interface contract, test environment or owning stakeholder is available. Integration risk is unbounded and unverifiable. |
| SCOPE-O-04 | Payment, billing or procurement handling | No stakeholder need identified in the CivicConnect scenario. |
| SCOPE-O-05 | Multi-language and localisation support | No stakeholder has stated a language need. Adds string management to every subsequent change. |
| SCOPE-O-06 | Offline / disconnected operation with local synchronisation | Conflict resolution and sync integrity are disproportionate to the value at this scale. |
| SCOPE-O-07 | AI-based automatic triage, classification or prioritisation of requests | Rejected as scope creep. No training data, no accuracy acceptance criterion, and it would place an unverifiable component on the critical accountability path. |
| SCOPE-O-08 | External contractor / third-party supplier portal | Introduces an additional trust boundary and authorisation model that the security work in scope cannot cover. |
| SCOPE-O-09 | IoT or sensor-originated automatic request creation | No such source exists in the described environment. |

## 4.3 Deferred

| ID | Item | Revisit | Reason and evidence required |
|---|---|---|---|
| SCOPE-D-01 | File and photograph attachments on a request | M2 (pending DEC-007) | Requires object storage beyond the free tier, file-type and size validation, malware handling, and a retention/privacy obligation for images that may contain personal data. Deferred until the platform decision (DEC-008) establishes actual free-tier storage limits and until evidence exists of how often a photograph is genuinely required. |
| SCOPE-D-02 | Automated SLA timers and escalation rules | M2 | FR-021 currently identifies overdue work against a target resolution time per category. The target values have not been agreed with a stakeholder (RSK-05). Automating escalation on unvalidated thresholds would generate false escalations and erode trust in the system. |
| SCOPE-D-03 | SMS / push notification channel | M4 or post-project | Returns when a funded messaging budget exists, or when a free-tier gateway is identified that meets the notification volume in NFR-013 at zero cost. Retained on the register so the unmet SH-04 escalation expectation (CF-03) stays visible; residual exposure is RSK-08. |
| SCOPE-D-04 | Anonymous or confidential reporting channel | M2 | Resolves CF-01 but requires a separate authorisation and audit model. Deferred pending a decision on whether accountability can be preserved without identity. |
| SCOPE-D-05 | Bulk import of historical spreadsheet and paper records | M3 | Data quality of the legacy records is unknown. Migration cannot be specified until the persistence design exists (M2) and a sample extract has been inspected. |
| SCOPE-D-06 | Advanced analytics, trend reporting and scheduled report distribution | M4 / future | FR-019 to FR-022 satisfy the stated oversight need. Further analytics adds query and performance load against NFR-001 for value not yet evidenced. |

## 4.4 A defended exclusion — no AI triage (SCOPE-O-07)

Automatic classification and prioritisation of requests was proposed during requirements drafting and rejected on four grounds:

1. No stakeholder need — it originated as an AI suggestion, not from the register (AI-002).
2. No acceptance criterion is possible. The team cannot state a defensible accuracy threshold or measure against labelled data, and a requirement without acceptance criteria cannot be baselined.
3. It would place an unverifiable component on the accountability path — the exact property the project exists to establish.
4. Inference at useful quality is not free, conflicting with CN-03, and creates a dependency the team does not control.

FR-026 was retained instead: a deterministic, testable duplicate warning on category and location. Same symptom, a fraction of the risk, and priced honestly as Could priority — the first requirement to drop under scope pressure.
