# Requirements Traceability Matrix

> **PED v1.0 section.** Owner: Don.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

All 40 baselined requirements are traced. Coverage is a control, not a statistic: a requirement absent from the matrix is one that nothing verifies, and a source producing no requirement is a need silently dropped. The four right-hand columns are deliberately empty — design references arrive in M2, issue, pull request and test identifiers in M3, release evidence in M4. Filling them now would be fabricated evidence.

| Trace | Source | Need | Req. | Pri. | AC | Verification | Design (M2) | Issue/PR (M3) | Test (M3) | Release (M4) | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TR-001 | SH-01 / Master Brief 2.0 - 'Requesters have limited visibility of whether a request was received' | Requester must know a request was received and where it stands | FR-005 | Must | AC-005 | Functional test + DB inspection | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-002 | SH-01 / Master Brief 2.0 | Requester must know a request was received and where it stands | FR-007 | Must | AC-007 | Functional test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-003 | SH-01 / Master Brief 2.0 | Requester must know a request was received and where it stands | FR-008 | Must | AC-008 | Functional + negative-access test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-004 | SH-01 / Master Brief 3.0 requester capabilities | Requester must receive meaningful feedback on acceptance, rejection, update and completion | FR-009 | Must | AC-009 | Functional test + notification log | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-005 | SH-04 / Master Brief 2.0 - 'Reporting is manual, inconsistent and difficult to audit' | Management must identify outstanding and overdue work reliably | FR-019 | Must | AC-019 | Functional test on seeded data | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-006 | SH-04 / Master Brief 2.0 | Management must identify outstanding and overdue work reliably | FR-021 | Must | AC-021 | Boundary test at T-1, T, T+1 | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined - threshold values provisional (RSK-05) |
| TR-007 | SH-04 / Master Brief 2.0 - 'weak accountability for changes to request status' | Every status and assignment change must be attributable | FR-025 | Must | AC-025 | Functional + negative test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-008 | SH-04, SH-09 / CN-05 | Every status and assignment change must be attributable | NFR-006 | Must | AC-N006 | Functional + negative test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-009 | SH-02 / Master Brief 2.0 - 'Staff have difficulty prioritising requests and identifying ownership' | Staff must see one prioritised queue with clear ownership | FR-011 | Must | AC-011 | Functional test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-010 | SH-02 / Master Brief 3.0 staff capabilities | Staff must locate relevant requests quickly | FR-012 | Must | AC-012 | Functional + performance test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-011 | SH-03 / Master Brief 3.0 staff capabilities | Ownership of a request must be unambiguous and changeable | FR-014 | Must | AC-014 | Functional test + audit inspection | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-012 | SH-04 / Master Brief 2.0 - 'no single controlled record of the lifecycle' | Status must move only through controlled transitions | FR-015 | Must | AC-015 | Full state-transition matrix test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-013 | SH-04 / CF-02 | Reporting must be possible by category without free-text noise | FR-006 | Must | AC-006 | Functional + boundary test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-014 | SH-04 / CF-02 | Reporting must be possible by category, status, assignee and period | FR-020 | Must | AC-020 | Functional test with reconciliation | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-015 | SH-09, CN-05 / CF-01 | Sensitive requester information must not be broadly visible | NFR-012 | Must | AC-N012 | Automated negative-access test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-016 | SH-05, CN-05 | Access must be restricted by role | FR-003 | Must | AC-003 | Role x operation matrix test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-017 | CN-05 / Master Brief 16 | Authorisation must be enforced, not assumed | NFR-004 | Must | AC-N004 | Automated matrix test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-018 | CN-05 / Master Brief 9 | No credential may exist in the repository | NFR-005 | Must | AC-N005 | Automated secret scan on every PR | N/A - control active from M1 | Active from M1 | Secret scan run | Pending M4 | Baselined - control operating |
| TR-019 | CN-03, SH-06 / Master Brief 4 | The solution must not create an unsustainable financial burden | NFR-010 | Must | AC-N010 | Cost review | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-020 | SH-02, SH-04 / CN-04 | The system must remain responsive at realistic volume | NFR-001 | Must | AC-N001 | Load test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-021 | SH-05 / Master Brief 3.0 management capabilities | Categories and their targets must be administrable | FR-023 | Must | AC-023 | Functional + referential-integrity test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-022 | SH-05 | Users and roles must be administrable | FR-024 | Must | AC-024 | Functional test + audit inspection | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-023 | SH-01, SH-02 / CF-04 | Requester and staff must communicate without exposing personal contact details | FR-010 | Should | AC-010 | Functional test + privacy review | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-024 | SH-02 / Master Brief 3.0 staff capabilities | Actions and resolution must be recorded against the request | FR-016 | Must | AC-016 | Functional test, positive and negative | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-025 | SH-02 / Master Brief 2.0 - 'requests may be duplicated' | Duplicate submissions should be reduced | FR-026 | Could | AC-026 | Functional test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined - lowest priority, first candidate for RSK-12 scope freeze |
| TR-026 | SH-05 / CN-05 | Accounts must exist and carry exactly one role | FR-001 | Must | AC-001 | Functional test + audit inspection | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-027 | SH-05, SH-09 / CN-05 | Only authenticated users may reach the system | FR-002 | Must | AC-002 | Automated negative-access test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-028 | SH-01 | A user locked out must be able to regain access safely | FR-004 | Should | AC-004 | Functional test, positive and negative | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-029 | SH-02 / Master Brief 3.0 staff capabilities | Staff must see complete request detail including history | FR-013 | Must | AC-013 | Functional test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-030 | SH-02, SH-04 / Master Brief 3.0 | Requests must be closed only by an authorised role | FR-017 | Must | AC-017 | Functional + authorisation test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-031 | SH-02 / Master Brief 3.0 requester capabilities | A rejected request must carry a reason back to the requester | FR-018 | Should | AC-018 | Functional test, positive and negative | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-032 | SH-04 / Master Brief 2.0 - 'Reporting is manual' | Management must be able to take activity data offline | FR-022 | Should | AC-022 | Functional + row-count reconciliation | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-033 | SH-01, SH-06 / CN-03 | The service must be reliably reachable during working hours | NFR-002 | Should | AC-N002 | Uptime monitoring log | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined - cold start declared as a known limitation (RSK-02) |
| TR-034 | SH-09 / CN-05 | Credentials must not be recoverable from storage | NFR-003 | Must | AC-N003 | Database inspection + code review | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-035 | SH-01 / Master Brief 3.0 | Submission must be achievable without training | NFR-007 | Should | AC-N007 | Moderated usability test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-036 | SH-01 | The service must be usable by people with visual or motor impairment | NFR-008 | Should | AC-N008 | Automated accessibility scan + keyboard walkthrough | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-037 | SH-07 / CN-04, CN-06 | The system must remain changeable by a three-person team | NFR-009 | Should | AC-N009 | CI coverage and static-analysis report | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-038 | SH-04, SH-06 / Master Brief 17 | Request data must survive loss of the environment | NFR-011 | Should | AC-N011 | Documented restore rehearsal | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-039 | SH-06 / CN-03 | The system must hold realistic volume inside free-tier limits | NFR-013 | Should | AC-N013 | Capacity test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |
| TR-040 | CN-05 / Master Brief 16 | Input must not be trusted from the client | NFR-014 | Must | AC-N014 | Automated boundary and negative test | Pending M2 | Pending M3 | Pending M3 | Pending M4 | Baselined |

Highlighted: TR-006 (FR-021) is baselined but carries a provisional threshold under RSK-05 — marked rather than presented as complete.

---

## Appendix A — End-to-End Trace: FR-025 (compiled PED appendix)

FR-025 carries the accountability property that is the core business value, and shows how one stakeholder need propagates into requirements, quality attributes, design constraints, risks and future verification.

| Stage | Evidence at v1.0 |
|---|---|
| Source | [1, §2] "There is weak accountability for changes to request status and actions taken." SH-04, supported by SH-09. |
| Requirement | FR-025 — record every status and assignment change with actor, timestamp, previous and new value; do not permit editing or deletion through the application. Must. |
| Quality requirement | NFR-006 — 100% of such changes recorded with all four fields, not modifiable through the application. |
| Acceptance criteria | AC-025 and AC-N006: for k changes the history shows exactly k ordered entries with all four fields, and no application function edits or deletes one. The negative half matters most — this requirement is about what the system must refuse to do. |
| Verification | Functional test, negative test and code review (M3). |
| Trace records | TR-007 (FR-025), TR-008 (NFR-006). |
| Dependencies | FR-014 and FR-015 must emit change events; FR-013 exposes history to authorised users; NFR-012 bounds who may read it. |
| Constraint interaction | CN-03 — an append-only trail grows monotonically against free-tier row capacity, interacting with NFR-013. Retention is open (FEC-05). |
| Design constraint | FEC-02 — transition logic must be separable from the UI, or audit behaviour is only testable end to end and NFR-009 coverage becomes unaffordable. |
| Risk | RSK-11 — the trail concentrates sensitive history, so NFR-012 must bound read access. |
| Decision | DEC-006 — authenticated submission only; without an identity there is no actor to record, so CF-01 was resolved in a way that preserves this requirement. |
| Still to come | M2 persistence design and enforcement point; M3 issue, pull request, test identifiers and results; M4 release evidence. |

A change to FR-025 after baseline would require revisiting NFR-006, FR-013, FR-014, FR-015, NFR-012, FEC-02, FEC-05, RSK-11 and DEC-006. The matrix makes that list discoverable rather than remembered.
