# Stakeholder Analysis

> **PED v1.0 section.** Owner: Masego.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

| ID | Stakeholder | Primary needs | Infl. | Int. |
|---|---|---|---|---|
| SH-01 | Requester (community member / staff submitting) | Submit a request quickly; know it was received; see progress without phoning; be told when it is done | Low | High |
| SH-02 | Service Staff / Technician | One prioritised queue; unambiguous ownership; full request detail; no duplicated or lost work | Medium | High |
| SH-03 | Service Coordinator / Supervisor | Assign and rebalance work; see ageing requests; prevent unassigned backlog | High | High |
| SH-04 | Operations Manager / Management oversight | Reliable and auditable information on outstanding, overdue, resolved and closed work; accountability for status changes; reporting that is not manual | High | High |
| SH-05 | System Administrator | Manage users and roles; maintain the controlled category list; control security configuration | Medium | High |
| SH-06 | Organisation / Project Sponsor | Improved visibility and accountability without unsustainable technical, operational or financial burden | High | Medium |
| SH-07 | Development Team (SEN381 registered team) | Deliverable scope within schedule and actual team capability; defensible engineering evidence | High | High |
| SH-08 | Lecturer / Assessor | Controlled, traceable and authentic engineering evidence produced progressively | High | High |
| SH-09 | Data subject (requester whose sensitive information is held) | Confidentiality of security-related, personal or HR-sensitive request content | Low | High |

Effort follows influence and interest. SH-03, SH-04, SH-07 and SH-08 are high on both and managed closely. SH-05 carries medium overall influence but high interest in its administrative domain — the controlled category list and role model that reporting (FR-020) and access control (NFR-004) depend on — and is managed closely there. SH-01 is low influence but high interest, and is the stakeholder most likely to abandon the system if visibility is poor — which is why status transparency is core scope rather than a convenience.

## 3.1 Competing expectations

A conflict is recorded only where the scenario evidences that both positions are genuinely held. Positions invented for balance were discarded (AI-006).

| ID | Conflict | Resolution | Implemented by |
|---|---|---|---|
| CF-01 | Requesters reporting security concerns want to submit anonymously to avoid reprisal. Management requires every request to be attributable for accountability and audit. | Authenticated submission only in v1. Requester identity is restricted to the assigned staff member, Manager and Administrator (NFR-012). An anonymous channel is explicitly deferred, not rejected. | DEC-006, FR-002, NFR-012, SCOPE-D-04, RSK-11 |
| CF-02 | Staff want the smallest possible submission form so requests are actually logged. Management wants rich structured data so reporting is meaningful. | Four mandatory fields only (title, description, category, location). Category is mandatory and drawn from a controlled single-level list; every other structured field is optional. Reporting depth is bought with category discipline rather than form length. | FR-005, FR-006, FR-020, DEC-012 |
| CF-03 | Management expects SMS / WhatsApp escalation for overdue work. No paid messaging gateway is available within the cost constraint. | Notification limited to in-app and email in v1. SMS deferred. The unmet expectation is carried openly as a risk rather than silently dropped. | FR-009, SCOPE-D-03, RSK-08 |
| CF-04 | Requesters want to contact the assigned technician directly. Staff and privacy interests require that personal contact details are not exposed. | All communication occurs in an in-app comment thread attached to the request record. No personal contact details are surfaced to requesters. | FR-010, NFR-012 |
| CF-05 | The sponsor requires zero recurring cost. Free-tier hosting introduces cold-start latency and capacity ceilings that threaten the performance and availability expectations of daily users. | Cost constraint is treated as binding. NFR-001 is specified against a warm instance and cold-start behaviour is declared as a known limitation rather than hidden. The architecture decision that resolves this is deliberately deferred to M2. | CN-03, NFR-001, NFR-002, RSK-02, DEC-008 |

## 3.2 From need to requirement

| Step | Content |
|---|---|
| Stakeholder | SH-04 Operations Manager (high influence, high interest) |
| Evidenced need | "Management has limited reliable information about outstanding, overdue and resolved work" [1, §2] |
| Requirement | FR-021 — identify a request as overdue when elapsed open time exceeds the configured target for its category |
| Acceptance criterion | AC-021 — open longer than target T in a non-terminal status is flagged; shorter is not. Tested at T−1, T, T+1 |
| Dependency created | FR-023 must make the target configurable, or FR-021 has nothing to measure against |
| Open issue | Target values are not agreed with any stakeholder (RSK-05); automated escalation deferred (SCOPE-D-02) |
| Still testable because | FR-021 is specified against a configurable value, so boundary testing works now and only the values are provisional |

One of forty such chains in the RTM. FR-025 is traced in full in Appendix A (see `docs/PED/07-traceability.md`).
