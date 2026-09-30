# Engineering Decision Log

> **PED v1.0 section.** Owner: Masego.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

Ten decisions taken, two deliberately deferred. A decision not actually made is recorded as deferred with the evidence required, rather than presented as decided.

| ID | Decision | Rationale | Trade-off accepted | Risk |
|---|---|---|---|---|
| DEC-001 | A - single controlled repository, protected main, pull request required, two approvals from members other than the author, no self-approval, linear history. | It is the mandated control, it produces the review evidence the milestone assesses, and one repository keeps documentation and future code under a single traceable history. | With three members, two approvals means unanimous consent from the other two; this is slower and creates a deadlock exposure. | RSK-04 |
| DEC-002 | B - the PED is authored as numbered Markdown sections in docs/PED/ and compiled to PED_v1.0.docx for submission and sign-off. | Markdown produces line-level diffs, so a reviewer can see exactly what changed and approve a specific change. A binary .docx cannot be merged or meaningfully reviewed, and option C guarantees an integration crisis at the deadline. | An extra compile-and-format step is needed before each baseline, and the submitted document must be regenerated rather than edited directly. | RSK-14 |
| DEC-003 | A - FR-nnn, NFR-nnn, AC-nnn, SH-nn, CF-nn, CN-nn, RSK-nn, DEC-nnn, FEC-nn, AS-nn, CHG-nnn, TST-nnn, DEF-nnn. Identifiers are never reused and never renumbered. | Stable flat identifiers survive reprioritisation and deletion. Hierarchical identifiers break as soon as a requirement is split or moved, which is exactly what happens between M1 and M2. | Identifiers carry no meaning, so a reader must consult the register rather than infer relationships from the number. | Low |
| DEC-004 | A - the AI Usage Register records material contributions with the verification actually performed, and the pull request template requires an AI declaration that the reviewer checks. | The assessed risk is unverified content entering the baseline, which applies at least as much to requirements and risk text as to code. Prohibition would be unenforceable and would waste a permitted engineering aid. | The register is only as good as the honesty of the entries, and maintaining it costs time on every substantive contribution. | RSK-07 |
| DEC-005 | A - registers are held as CSV under docs/, and a compiled .xlsx is generated for presentation and submission. | CSV changes appear as reviewable diffs, so a risk being downgraded or a requirement being edited is visible to reviewers. A workbook is opaque in review, and tables embedded only in the PED cannot be maintained between baselines. | Two representations must be kept in step, and the workbook must be regenerated rather than edited. | RSK-14 |
| DEC-006 | A - all submissions are authenticated in v1. Identity is protected by restricted visibility (NFR-012) rather than by absence of identity. A confidential channel is deferred (SCOPE-D-04). | Accountability and audit are the core business need in the CivicConnect scenario, and an anonymous request cannot be clarified, updated or fed back on, which breaks FR-009 and FR-010. Option C requires a second authorisation model that the M1 scope cannot support. | The reprisal concern raised by SH-01 is not fully resolved and remains open on the deferred register. | RSK-11 |
| DEC-009 | A - MoSCoW, with Must reserved for requirements without which the minimum business capabilities in Master Project Brief section 3 are not met. | MoSCoW makes the contingency in RSK-12 executable: under pressure the team drops Could and Should items in a defined order rather than negotiating individually. A numeric scale invites everything to be rated 5. | MoSCoW carries no ordering within a band, so sequencing still requires the backlog. | Low |
| DEC-010 | A - documented in docs/governance/team-working-agreement.md and agreed by all three members. | A fixed turnaround makes review latency predictable, and small pull requests make review cheap enough to actually perform properly. Batched review would concentrate risk immediately before the milestone. | Requires daily engagement from all three members regardless of whose workstream is active. | RSK-04, RSK-09 |
| DEC-011 | A - the Coordinator responsibilities of SH-03 are served by the Manager role in v1. | A fifth role multiplies the authorisation test matrix in NFR-004 for a separation of duty that no stakeholder has stated as a need. Scope discipline favours the smaller controlled model. | If assignment volume grows, Managers carry coordination workload that a dedicated role would absorb; SH-03 needs are met functionally but not organisationally. | Low |
| DEC-012 | A - a single-level controlled list, administered under FR-023. | A single level keeps the submission form to one selector, keeps FR-020 reporting reconcilable, and keeps the target resolution time in FR-021 attached to exactly one level. Two levels double the administration and create ambiguous parent-level reporting. | Reporting granularity is limited to the top level, which SH-04 may find coarse once real volume exists. | Low |

## 10.1 Deferred decisions

Deferring is acceptable and often correct where the team can state the evidence still required [2, §4]. Neither of these is an omission.

### DEC-007 — File and photograph attachments

| | |
|---|---|
| Context | Attachments would materially improve fault reporting, but introduce storage cost, malware exposure and a retention obligation. |
| Status | DEFERRED - decision to be taken at M2 once the platform decision establishes actual free-tier storage limits. |
| Why deferring is correct | Committing now would bind the M2 platform choice to a storage requirement whose cost is unknown, which inverts the correct decision order. |
| Consequence accepted | Fault reports remain text-only in the interim, which SH-02 may find limiting. |
| Evidence required | Free-tier object-storage limits of candidate platforms; frequency with which a photograph is genuinely needed; malware-scanning options at zero cost; retention rules for images containing personal data. |
| What it determines | Affects persistence design, upload validation, security testing and operational cost from M2 onwards. |
| Risk | RSK-08, RSK-02 |

### DEC-008 — Technology stack, architecture and deployment platform

| | |
|---|---|
| Context | These are the most consequential technical decisions in the project and are explicitly outside the M1 boundary. |
| Status | DEFERRED to M2, to be taken through a weighted decision matrix and an Architecture Decision Record supported by a measured proof of concept. |
| Why deferring is correct | The evidence required to choose well does not exist yet. Baselined requirements and NFRs are inputs to the decision, not outputs of it. Choosing a stack in M1 would be a preference exercise rather than an engineering decision, and the Master Project Brief makes technology selection an assessed decision. |
| Consequence accepted | The team cannot begin construction, which compresses M2. Accepted deliberately. |
| Evidence required | Verified availability and compatibility on the Belgium Campus desktop platform; free-tier limits and cold-start behaviour of candidate hosts; an honest team capability audit; a small proof of concept exercising authentication, persistence and deployment. |
| What it determines | Determines architecture, persistence, CI, deployment, operational cost and the achievability of NFR-001, NFR-002, NFR-010 and NFR-013. |
| Risk | RSK-02, RSK-03, RSK-12 |
