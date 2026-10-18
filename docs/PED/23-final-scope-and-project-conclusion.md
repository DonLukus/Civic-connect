# 23. Final scope, acceptance and project conclusion - PED v4.0 review candidate

**Group U. Deadline: 18 October 2026 (reported by Emile). Status: substantive closure prepared for independent review; not a signed submission or new team release decision.** This section continues sections 00-22. Historical approvals retain their original scope.

## 23.1 Product and evidence identity

Active repository: https://github.com/DonLukus/Civic-connect. Verified application source: `98b1c55700d940f915d856119f581adee8044986`. It adds the minimal DEF-006 privacy fix and TST-051/052 to main `af2f5456a9a940f6c9a020db5cd5fe5e4889219d`. The current closure documentation is on `docs/emile-m4-closure`; the final assessed documentation commit/tag must be selected after review. PR #92 is a separate README correction; do not assume it merged.

The two live HTTP journeys and local load/recovery reports are indexed in [docs/release/evidence/2026-10-18/verification-summary.json](../release/evidence/2026-10-18/verification-summary.json). Results identify exact source hashes; no machine execution is attributed to a student personally. This is not a new feature programme.

### Fresh verification on the assessed application candidate

| Check | Actual observed result | Boundary |
|---|---|---|
| Automated suite | 62 passed in 128.48 seconds | Includes 60 prior cases and two risk-driven final regressions; no browser-automation claim |
| CI suite and retained coverage | 62 passed in 38.81 seconds; 78.50%, 70% threshold passed | [Run 39091537311](https://github.com/DonLukus/Civic-connect/actions/runs/39091537311) on 52e175ba, Python 3.11; XML/JSON artifact 12122139293. Required-check settings remain separate. |
| Persistence line coverage | 230/293 lines, 78.4983% | Includes lifecycle, outbox, earlier repository and both service modules |
| Five-minute warm list load | 13,212/13,212 successes; zero failures; p95 0.281 seconds | 10 Staff users, exactly 500 filtered records, 300 seconds, local Waitress; no cold-start/hosted-capacity claim |
| Two existing live HTTP journeys | Passed; notification observed in 1.125 seconds | Real loopback HTTP and local STARTTLS sink, not an external inbox or human browser session |
| Local stop/start | Accepted request 501 retained | Same isolated SQLite file; not cloud redeploy |
| Online backup/separate restore | Integrity OK; 501 requests, 502 audit rows, 1 outbox row preserved | Timed local drill; no daily schedule, retention or schema rollback claim |
| Static/dependency checks | Ruff clean; Bandit no findings; no known dependency findings | Tool/advisory scope at check time |
| Explicit history scan | Latest run: 179 commits scanned, no leaks found | Manual run 39091537311 on 52e175ba; earlier application run scanned 174. Existing exact false-positive ignore retained; separate from old zero-commit range run. |
| Accessibility subset | Four submission fields labelled; four declared colour pairs >=4.5:1 | No computed-style browser audit or human keyboard/usability acceptance |

## 23.2 Original baseline, controlled changes and scope result

The approved M1 record contains 26 FR, 14 NFR and 40 unique AC references. M1 is dated 8 September 2026. A pre-CHG-001 content snapshot at `52913f7121bfde410f1ec081665bd86a9ae80c98` was compared against current controlled CSVs: requirement wording and priorities are unchanged; only AC-009 and AC-014 differ, as documented by CHG-001. Snapshot provenance is not a fabricated historical release SHA.

CHG-002 approves a narrower supervised evaluation slice; it explicitly retains unfulfilled baseline obligations. No acceptance criterion is removed from this denominator. Original out-of-scope and deferred items are not added as failures. M2 remains Proposed where the baseline file says so; ADR-001/007 and DEC-008/013/018 do not become Accepted/Decided merely by merging code or this closure.

**Proposed QA scope completion: 40.00% = 16/40 points.** 9 criteria are assessed Met, 14 Partially Met and 17 Not Met. Met=1, Partially Met=0.5, Not Met=0. Scores are unweighted AC judgments, not test counts, and remain subject to independent review. **The 80% target is not demonstrated.** The large original-scope variance is a material final outcome, not corrected by renaming partial delivery as complete. Every unmet Must criterion stays visible in the RTM.

## 23.3 M1 scope to final delivery

| Original scope | Current outcome | Evidence and stakeholder consequence |
|---|---|---|
| SCOPE-I-01 - Authentication and role-based access control for four roles: Requester, Staff, Manager, Administrator | PARTIALLY IMPLEMENTED | Requester registration/login and four-role guards exist. Password reset and operational Administrator account functions remain absent. |
| SCOPE-I-02 - Service request submission with a mandatory controlled category | IMPLEMENTED for original submission ACs | Required fields, active controlled category, reference, New state and receipt have test/live evidence. Category administration remains a separate gap. |
| SCOPE-I-03 - Requester visibility: current status and full history of own requests | PARTIALLY IMPLEMENTED | Own list/detail/status exists; later resolution note/lifecycle commitments are incomplete. |
| SCOPE-I-04 - In-app and email notification on accept, reject, update and completion | PARTIALLY IMPLEMENTED | Acceptance in-app/local SMTP works; rejected/resolved/comment triggers and external inbox assurance remain incomplete. |
| SCOPE-I-05 - Staff work queue with search, filter and sort | PARTIALLY IMPLEMENTED | Staff queue/status filter/detail exists; broad search, combined filters, sorting and full comments/history are incomplete. |
| SCOPE-I-06 - Assignment, self-assignment and reassignment of requests | PARTIALLY IMPLEMENTED | Staff self-accept/version guard exists; Manager assignment and reassignment remain absent. |
| SCOPE-I-07 - Controlled status lifecycle enforced as a state machine | PARTIALLY IMPLEMENTED | Only New-to-Accepted is built. The complete seven-state permitted/forbidden matrix is not delivered. |
| SCOPE-I-08 - Action, comment and resolution recording on a request | NOT IMPLEMENTED | Actions, comments and resolution recording are unavailable; no full completion workflow. |
| SCOPE-I-09 - Management dashboard covering open, in progress, overdue, resolved and closed work | NOT IMPLEMENTED | Management open/overdue/resolved/closed counts and overdue identification are unavailable. |
| SCOPE-I-10 - Breakdown of activity by category, status, assignee and period, with CSV export | NOT IMPLEMENTED | Activity breakdown and filtered CSV export are unavailable. |
| SCOPE-I-11 - Administration of the controlled category list and of users and roles | NOT IMPLEMENTED operational administration | Bootstrap seeds categories/users; it is not create/rename/deactivate/category-target or role/deactivation administration. |
| SCOPE-I-12 - Immutable audit trail of status and assignment changes | PARTIALLY IMPLEMENTED | Submission/acceptance audit exists with actor IDs; later transition/reassignment obligations remain incomplete. |

Nine exclusions and six deferrals remain separately recorded in the existing scope baseline. All 14 NFRs are included in the AC denominator, even where they are not listed in a functional scope group. No untested NFR is silently excluded.

## 23.4 Criterion-by-criterion outcome

The existing RTM owns the detailed final QA fields; this table is its generated PED view, not a new RTM. Full original/current AC wording remains in section 06 and the controlled CSVs.

| Requirement / AC | Priority | Proposed outcome / points | Evidence or limiting conclusion |
|---|---|---|---|
| FR-001 / AC-001 | Must | NOT MET / 0 | Original AC is Administrator account creation/one-role/audit: not implemented. Self-registration is delivered but is not that AC. |
| FR-002 / AC-002 | Must | PARTIALLY MET / 0.5 | Login/session checks work; public registration is an approved demo addition but the original sign-in/reset-only AC has not been formally rewritten. Partial pending explicit final AC reconciliation. |
| FR-003 / AC-003 | Must | MET / 1 | Four roles and existing-operation matrix verified; TST-052 also confirms deactivation revokes access. This does not supply missing operational features. |
| FR-004 / AC-004 | Should | NOT MET / 0 | Single-use, expiring emailed password reset is not implemented. Implement only if prioritised within remaining approved work; otherwise record unmet status and user consequence. |
| FR-005 / AC-005 | Must | MET / 1 | Required fields, controlled category, New state, submitter/reference/time and receipt have existing tests and live HTTP evidence. |
| FR-006 / AC-006 | Must | MET / 1 | Active-list selection and invalid/missing-category rejection verified. Administrator maintenance remains a separate unmet FR-023 obligation. |
| FR-007 / AC-007 | Must | PARTIALLY MET / 0.5 | Own list/detail/status exists. Confirm status-change date and the original resolution-note clause; later resolution functionality remains outside the current slice. |
| FR-008 / AC-008 | Must | MET / 1 | Own recent-first list, fields and isolation are implemented and covered; stale TR-003 missing-list claim superseded. |
| FR-009 / AC-009 | Must | PARTIALLY MET / 0.5 | Acceptance in-app/local-SMTP evidence exists. Rejected, resolved and comment triggers plus intended external delivery remain incomplete/unverified; use CHG-001 AC wording. |
| FR-010 / AC-010 | Should | NOT MET / 0 | Requester/assigned-Staff comments with author/time and contact privacy are not implemented. |
| FR-011 / AC-011 | Must | MET / 1 | Unassigned and own-assigned Staff queue partitions have passing service/route evidence. |
| FR-012 / AC-012 | Must | PARTIALLY MET / 0.5 | Status filtering exists; reference/keyword search, combined category/assignee/priority/date filters and requested sorting remain incomplete. |
| FR-013 / AC-013 | Must | PARTIALLY MET / 0.5 | Detail and creation/acceptance history exist. Comments and complete later lifecycle/assignment history are not fully delivered. |
| FR-014 / AC-014 | Must | PARTIALLY MET / 0.5 | Staff self-accept/version check exists. Manager assignment and reassignment, unaffected status on reassignment and prior/new assignee audit remain incomplete. |
| FR-015 / AC-015 | Must | PARTIALLY MET / 0.5 | Only New-to-Accepted is implemented/specified for the slice. Remaining legal/forbidden transitions and original Closed/reopen AC are not established. |
| FR-016 / AC-016 | Must | NOT MET / 0 | Staff action/resolution recording and required resolution note are not implemented. |
| FR-017 / AC-017 | Must | NOT MET / 0 | Staff resolution and Manager closure with role negatives/audit are not implemented. |
| FR-018 / AC-018 | Should | NOT MET / 0 | Reject/return with mandatory reason and linked Requester notification is not implemented. |
| FR-019 / AC-019 | Must | NOT MET / 0 | Period-based management dashboard counts are not implemented. |
| FR-020 / AC-020 | Must | NOT MET / 0 | Category/status/assignee/time-period activity breakdown and reconciliation are not implemented. |
| FR-021 / AC-021 | Must | NOT MET / 0 | Overdue identification against category targets is not implemented; target authority remains RSK-05. Do not invent authorised values. |
| FR-022 / AC-022 | Should | NOT MET / 0 | Filtered-list CSV export and exact row/field reconciliation are not implemented. |
| FR-023 / AC-023 | Must | NOT MET / 0 | Operational category create/rename/deactivate/target management and referential-integrity behaviour are not implemented. |
| FR-024 / AC-024 | Must | NOT MET / 0 | Operational role change/deactivation, loss of sign-in, Manager reassignment visibility and change audit are not implemented. |
| FR-025 / AC-025 | Must | PARTIALLY MET / 0.5 | Creation/acceptance audit exists. Complete lifecycle/reassignment coverage remains partial; finalise k-change counting, actor/UTC/prior/new values and edit/delete negative evidence. |
| FR-026 / AC-026 | Could | NOT MET / 0 | Same-category/location duplicate warning and confirm/cancel flow are not implemented. Preserve Could priority and any actual approved disposition. |
| NFR-001 / AC-N001 | Must | PARTIALLY MET / 0.5 | Five-minute 500-record/10-user warm local scenario is rerun/confirmed separately in the evidence summary. Cold-start measurement is still absent; full compound AC therefore partial. |
| NFR-002 / AC-N002 | Should | NOT MET / 0 | Weekday 07:00-18:00 SAST, >=95% staging availability over the M3 evaluation period and observed cold-start evidence are not established. State the real boundary; do not fabricate an elapsed-period uptime log. |
| NFR-003 / AC-N003 | Must | PARTIALLY MET / 0.5 | Fresh bcrypt accounts verified; legacy-hash fixture/login migration exists but dormant historical account storage has no accepted migration/reset disposition. |
| NFR-004 / AC-N004 | Must | MET / 1 | Existing-operation role matrix and new mid-session deactivation control pass. Missing operations are not counted as tested. |
| NFR-005 / AC-N005 | Must | MET / 1 | Manual quality run 39091537311 on 52e175ba scanned 179 commits with no leaks found, using the existing exact false-positive fingerprint ignore and no restricted log range. Earlier application-only run 39090851534 scanned 174 commits. Platform push protection/bypass and final review remain separate. |
| NFR-006 / AC-N006 | Must | PARTIALLY MET / 0.5 | Audit evidence covers the constructed slice. Confirm exact change sequence, actor/UTC/prior/new values and denied modification on final operations; later transitions/reassignments remain unavailable. |
| NFR-007 / AC-N007 | Should | NOT MET / 0 | No completed moderated 5-participant usability evidence was identified. The original criterion is >=4 unaided valid submissions within 3 minutes; do not substitute AI execution or a single rehearsed demonstration. |
| NFR-008 / AC-N008 | Should | PARTIALLY MET / 0.5 | Four labelled visible submission controls and four declared CSS contrast pairs pass a bounded automated check. No computed-style browser scan or human keyboard walkthrough; partial only. |
| NFR-009 / AC-N009 | Should | MET / 1 | CI run 39091537311 on 52e175ba reports 62 passing tests and 230/293 persistence lines covered (78.4983%); the 70% threshold passes and XML/JSON coverage artifacts are retained. Source Bandit has no findings and dependency audit passes; local Ruff is clean. This candidate result is not a claim that branch-protection required-check settings are enabled or that it has merged to main. |
| NFR-010 / AC-N010 | Must | NOT MET / 0 | Conclude R0 recurring-cost evidence, every service/free-tier limit/consumption and projection at 100 active users / 1,000 monthly requests. Resolve any storage/hosting-cost conflict without silently adopting a paid service. |
| NFR-011 / AC-N011 | Should | PARTIALLY MET / 0.5 | Fresh local online backup/separate restore passed in 0.031 seconds with integrity OK and matching 501 request, 502 audit and one outbox row counts. Daily scheduling/retention, hosted durability and recovery from an earlier point are not evidenced; the complete original AC remains partial. |
| NFR-012 / AC-N012 | Must | MET / 1 | DEF-006 nested email projection removed. Existing cross-requester/role checks plus TST-051 nested privacy and TST-052 inactive-session denial pass for the implemented interfaces. |
| NFR-013 / AC-N013 | Should | NOT MET / 0 | 500 users plus 5,000 requests within documented storage limits while the NFR-001 test passes has not been demonstrated. Retain this distinction from the existing 500-request load result. |
| NFR-014 / AC-N014 | Must | PARTIALLY MET / 0.5 | Server validation/CSRF and registration boundaries have tests. Confirm every implemented input has boundary/invalid-type coverage, field-level messages and retained non-secret form values; do not infer full acceptance from selected cases. |

## 23.5 M3 issue and register conclusion

DEF-004/005 fixes are merged and their automated regressions have been rerun. DEF-003's broad catch now logs exceptions but remains a retained error-classification concern; it is not falsely marked repaid. DEF-006 nested service data leakage is corrected by excluding unnecessary email projection; the current HTML template was not demonstrated to render that value. TST-051 failed before the fix and passes after it. TST-052 confirms deactivated users lose existing-session and direct-service access.

The existing risk and assumption CSVs now have dated closure-observation fields; they do not turn unverified mitigations into accepted facts. Existing TD-001..006 remain retained where recovery, durability, legacy hashes, missing functions or rollback still need work. The role matrix part of TD-005 is addressed; browser/keyboard/uptime/capacity limitations remain. The decision log retains actual Proposed/Deferred states and records consequences. AI-049/050 state actual assistance and checks, not new student votes.

## 23.6 Deployment / no-go assessment for team decision

**QA recommendation: remain in isolated simulated staging; NO-GO for public production. Team decision: PENDING.** The existing loopback Waitress/SQLite/local-STARTTLS environment is separated from development, uses synthetic accounts and ignored secrets and has reproducible commands. It is not public HTTPS, external mail or hosted persistence.

| Blocking concern | Requirement/risk/debt | Consequence if released | What would change the decision |
|---|---|---|---|
| Hosted persistence not verified | NFR-011; TD-002; DEC-008 | Request/audit data may be lost on host restart/redeploy | Select and verify durable storage and restore on the actual host |
| Outbox crash/retry recovery | FR-009; TD-001 | Stuck notifications or duplicate external mail | Failure-injection evidence and an accepted recovery/idempotency policy |
| Historical credential and external transport boundaries | NFR-003; TD-003; FR-009 | Inconsistent stored hashes or unverified external delivery/TLS | Inspect/migrate actual release data and verify intended SMTP environment |
| Broad baseline scope remains undelivered | Original Must requirements; CHG-002 | Management, administration and lifecycle stakeholder needs remain unmet | Realistic completion or explicit accepted change/limitation; no invented completion score |

This is a reasoned recommendation, not a new vote by Don or Masego. A justified no-go can satisfy the brief's deployment-decision expectation while still honestly reporting scope loss. No new paid host, database adoption, daily backup infrastructure or monitoring system is introduced solely for M4.

## 23.7 Significant decisions and project conclusion

1. A single server-rendered Flask deployment reduced UI/API integration overhead and enabled real HTTP journeys. It did not establish final hosting suitability; ADR-001 and DEC-008 remain open.
2. Transactional version/state/audit/outbox changes made acceptance race checks and notification failure separation demonstrable. In-process worker simplicity left stuck-sending/duplicate-delivery debt; an outbox is neither event sourcing nor exactly-once mail.
3. Restricting the supervised slice produced a coherent demonstration, but left many original Must commitments incomplete. The measured AC result must govern the final conclusion; reviewing a demo slice did not erase the original baseline.

The project delivered a useful, integrated Requester-to-Staff acceptance path with persistent local data, controlled access, attributable acceptance and measurable local evidence. It did not deliver the whole service-management product or prove public-production readiness. The most important next work is the unmet original workflow/management/admin scope, decision closure and durable/operational assurance, rather than optional new features. No assessment mark is predicted.

## 23.8 Combined demonstration and individual defence preparation

Use the final reviewed reference, not separate student prototypes. The brief's guide totals about 24 minutes: product journeys (6), M1-to-delivery scope and percentage (6), M3 fixes/limitations (4), selected acceptance traces (4), conclusion/decision consequences (4). Confirm the actual session allocation. Existing staging runbook supplies commands and locally generated synthetic credentials; do not put those credentials in the PED or slides.

| Student | Evidence to navigate and explain |
|---|---|
| Emile | FR-014/AC-014 -> version guard -> acceptance test/live journey -> audit/outbox -> partial scope; NFR-001 workload and p95 method; continuing PDF and actual AI verification boundaries |
| Don | State/audit/outbox transaction, proposed vs accepted ADRs, host/durability limits, actual rulesets/CI and a meaningful failure/recovery trade-off |
| Masego | Original AC versus test assertions, role/ownership matrix and new regressions, final RTM/partial scores, defect closure and privacy/keyboard/usability evidence limits |

Each student should show their actual contribution, one requirement-to-final-evidence trace, a decision outside their own component, one resolved and one retained issue, a failure/change response and a concise evidence-based conclusion. These are preparation notes, not a claim that rehearsal or human defence has occurred.

## 23.9 Final submission information and remaining gates

| Field | Current record |
|---|---|
| Team name / number | Group U (provided by Emile) |
| Members | Emile, Don, Masego; confirm institutional identifiers if Moodle requires them |
| Repository | https://github.com/DonLukus/Civic-connect |
| Assessed application candidate | 98b1c55700d940f915d856119f581adee8044986 |
| Final commit / tag / release | PENDING final review and team freeze; do not submit the candidate label as an approved release |
| PED | v4.0 review candidate, continuing the existing PED; promote to Final only after actual review |
| Final RTM | docs/requirements/RTM.csv - 40 original records with proposed final QA fields |
| Product access | Local staging demonstration per docs/deployment/m3-staging.md; no new public production URL |
| Official deadline | 18 October 2026, supplied by Emile; exact Moodle cutoff time not supplied |
| Actual submission date / receipt | PENDING actual submission; no submission claimed |

Before submission: obtain independent review, confirm/adjust AC judgments, record the real team deployment decision, freeze the exact assessed documentation/product reference, inspect the final PDF and check assessor access. Upload PED v4.0 Final, correct repository URL, exact final reference and any specifically required access information to Moodle; preserve the receipt. No separate code ZIP unless instructed. Do not change the assessed baseline after the deadline without explicit authorisation.
