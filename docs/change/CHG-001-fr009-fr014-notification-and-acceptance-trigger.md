# Change Request CHG-001

Template per Master Project Brief Appendix E. Required for any change to baselined scope,
requirements or acceptance criteria after PED v1.0.

| Field | Value |
|---|---|
| Change ID | CHG-001 |
| Requested by | Emile, during the M2 baseline review (brief §5.1) |
| Date | 2026-09-30 |
| Requested change | Two related acceptance-criteria clarifications, both already surfaced and agreed by the team during Assignment 2 (§5.1) but never written back into the baselined requirements: (1) FR-009's acceptance criterion doesn't cover the "updated with a comment" trigger the requirement text itself names — only status changes to Accepted/Rejected/Resolved; (2) neither FR-014 nor FR-015 states which action actually moves a request from New to Accepted. |
| Reason / expected value | These are gaps in what "Accepted" gets counted as, not new scope. Leaving them open into M2 means the persistence and design-pattern ADRs (status-lifecycle validator, notification observer) would be built against an ambiguous requirement. Closing it now, before those ADRs are written, avoids the ADRs encoding an assumption that was never actually approved. |

## Impact analysis

| Area | Impact |
|---|---|
| Requirements affected | FR-009 (AC-009), FR-014 (AC-014). Wording only — no new FR/NFR, no priority change. |
| Acceptance criteria affected | AC-009 broadened to include a comment-added trigger. AC-014 states explicitly that both a Staff self-accept and a Manager's initial assignment move status New → Accepted (and trigger FR-009); a Manager reassigning an already-assigned request changes only the assignee, not the status. |
| Architecture / design affected | None yet — but this is exactly the ambiguity the M2 status-lifecycle and notification design decisions would otherwise have had to guess at. Closing it here means ADR-003/ADR-004 can cite a settled requirement. |
| UI / API / data affected | None at this stage (pre-implementation). |
| Data migration | None. |
| Security & privacy impact | None. |
| Quality & testing impact | AC-009's and AC-014's test cases (functional test + notification log; functional test + audit inspection) now have a fully specified condition to test against instead of an implicit one. |
| Regression impact | None — no prior implementation exists to regress. |
| Scope impact | None — clarifies existing Must-priority requirements, doesn't add or remove capability. |
| Schedule & resource impact | None. |
| Cost impact | None. |
| Deployment & operations impact | None. |
| Risk impact | Reduces RSK-08 slightly (deferred-expectation risk) by removing an ambiguity that would otherwise surface as a defect or a disputed assumption later. |
| Technical debt impact | Prevents debt — this closes a gap before code exists, rather than after. |

## Decision

| Field | Value |
|---|---|
| Recommendation | ACCEPT |
| Rationale | Both clarifications restate a reading the whole team already reached and used in Assignment 2 (§5.1, signed off 2026-09-15) — this change request just puts that reading into the controlled requirement text and acceptance criteria where DEC-004 says it belongs, rather than leaving it live only inside an assignment document. |
| Approved by | Don, Masego (both already agreed this reading in A2; formal sign-off via PR review) |
| Date | 2026-09-30 |

## Post-implementation

- [x] Requirements and acceptance criteria updated (`docs/requirements/functional-requirements.csv`, `docs/PED/06-requirements.md`)
- [x] RTM updated (`docs/requirements/RTM.csv`, TR-004 and TR-011 status notes)
- [ ] Affected registers updated — none affected beyond requirements/RTM
- [x] PED version incremented and version history entry added (`docs/PED/00-document-control.md`, v2.0 row)
- [x] Decision log entry created (`docs/PED/10-decision-log.md` §10.3)
