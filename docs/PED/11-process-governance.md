# Engineering Process and Team Governance

> **PED v1.0 section.** Owner: Emile.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

Short milestone-aligned increments with a controlled baseline at each gate. With three part-time engineers, the process elements that earn their cost are a shared issue backlog, small reviewable changes, a fixed review cadence and a formal gate.

## 11.1 Team working agreement (DEC-010)

| Area | Agreement |
|---|---|
| Ownership | Masego: problem, stakeholders, scope, constraints, decisions. Don: requirements, acceptance criteria, RTM, forward engineering, repository setup and governance. Emile: risk, AI control, working agreement, document control, PED assembly and baseline. Ownership is drafting responsibility, not exclusive knowledge. |
| Review turnaround | 24 hours, with a fixed daily review window so review is never the thing that waits. |
| Change size | Small and single-purpose. A change that cannot be reviewed properly in fifteen minutes is split. |
| Approval | Two approvals from members other than the author. No self-approval, no administrator bypass. |
| Absence | Planned absence announced 24 hours ahead with reviews cleared first. Unplanned absence beyond 48 hours is escalated to the lecturer rather than resolved by weakening the control (RSK-04). |
| Cross-review | Each member reviews both other workstreams — no member reviews only their own area, which would guarantee RSK-13. |
| Individual evidence | Each member authors ≥1 pull request, meaningfully reviews ≥2, owns issues, can trace one requirement end to end, and can explain one decision and one AI verification that are not their own. |
| Disagreement | Resolved by evidence. Where evidence is unavailable the decision is deferred with the evidence required stated — the standard applied to DEC-007 and DEC-008. |
| Done | Reviewed and approved by two members, identifiers consistent, RTM and affected registers updated, project history entry written. |

## 11.2 Change control from this baseline

The procedure and template exist now, before the first change request arrives — the mitigation for RSK-01 [1, §14].

| Step | Action | Evidence |
|---|---|---|
| 1 Raise | Logged with a CHG- identifier, requester, date, expected value | Change request record |
| 2 Impact | Requirements and acceptance criteria, architecture, UI, data and migration, API contracts, security and privacy, scope, schedule, cost, testing and regression, deployment and operations, risk and debt | Impact analysis |
| 3 Decide | Accept, modify, defer or reject, with rationale | Decision log entry |
| 4 Authorise | Two approvals from non-authors | Pull request approvals |
| 5 Implement | On a branch referencing the CHG- identifier | Commits, pull request |
| 6 Verify | Acceptance criteria re-verified; regression considered | Test evidence |
| 7 Baseline | PED version incremented; RTM and registers updated | New version, RTM diff |
