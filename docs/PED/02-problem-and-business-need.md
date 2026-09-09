# Problem Statement and Business Need

> **PED v1.0 section.** Owner: Masego.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

The organisation does not have a service request problem; it has an information control problem. Requests arrive by email, telephone, WhatsApp, spreadsheet and paper. Each channel holds a partial record, none holds the whole record, and none enforces a lifecycle. Every symptom follows from that single cause.

| Symptom [1, §2] | Engineering cause | Addressed by |
|---|---|---|
| Requests duplicated, overlooked, misassigned or lost | No authoritative record; no controlled intake point | FR-005, FR-026 |
| Requesters have limited visibility of status | Status held in people, not in a queryable system | FR-007, FR-008, FR-009 |
| Staff cannot prioritise or identify ownership | No assignment model; no shared prioritised view | FR-011, FR-012, FR-014 |
| Weak accountability for status changes | No audit of who changed what and when | FR-025, NFR-006 |
| Management lacks outstanding/overdue information | No consistent state model, so aggregation is impossible | FR-019, FR-020, FR-021 |
| Reporting is manual and hard to audit | Data re-keyed between channels; no single source | FR-020, FR-022 |
| Sensitive information handled inconsistently | No access boundary around request content | FR-003, NFR-004, NFR-012 |
| No controlled record of a request lifecycle | The lifecycle is undefined and therefore unenforceable | FR-015 |

This is why the scope baseline takes the shape it does. Consolidating onto one controlled record with an enforced lifecycle and an audit trail addresses the cause; adding channels would treat symptoms while worsening the cause, which is why SCOPE-O-02 excludes WhatsApp and SMS intake.

## 2.1 Business need and value

The organisation needs a controlled platform to submit, manage, monitor and report on service requests, improving visibility and accountability "without creating an unsustainable technical, operational or financial burden" [1, §2.1]. The second clause is a constraint, not an aspiration: it makes CN-03 binding, rules out paid always-on infrastructure, and forces the deferment in SCOPE-D-01.

| Value | For | Judged by |
|---|---|---|
| Requests stop being lost — one record replaces five channels | SH-01, 02, 06 | Every request has a reference and a state at all times (FR-005, FR-015) |
| Visibility without chasing | SH-01 | A requester answers "where is my request" unaided (NFR-007) |
| Ownership becomes explicit | SH-02, 03 | No request sits in a non-terminal state without an owner (FR-014) |
| Accountability becomes evidential | SH-04, 09 | Any status change is attributable after the fact (FR-025, NFR-006) |
| Reporting stops being manual | SH-04 | Dashboard figures reconcile to stored records (FR-019, FR-020) |
| Sensitive information is bounded | SH-09 | Negative-access tests pass for every role (NFR-004, NFR-012) |

## 2.2 Success beyond working code

Stated now so it can be evaluated honestly in M4 rather than invented then [1, §5]:

- Every request has a complete, attributable lifecycle record from submission to closure — evidenced by the audit trail, not asserted.
- A manager can answer what is outstanding, overdue and owned by whom from the system alone, and the figures reconcile to stored records.
- Delivered scope matches the approved baseline, and every deviation traces to an approved change request.
