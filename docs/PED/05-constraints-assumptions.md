# Constraints and Assumptions

> **PED v1.0 section.** Owner: Masego.
> Authored here in Markdown and compiled to `docs/PED/exports/PED_v1.0.docx` (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

| ID | Type | Constraint | Engineering implication |
|---|---|---|---|
| CN-01 | Scope | Committed scope must be baselined and controlled. Minimum business capabilities in the Master Project Brief section 3 must be delivered. Uncontrolled scope creep is not acceptable. | Every requirement must trace to a stakeholder source. Additional features enter only through a change request with impact analysis. Six items were deliberately deferred rather than absorbed. |
| CN-02 | Schedule | Four assessed milestones inside a single SEN381 delivery period. Three part-time student engineers with concurrent modules. | M1 must be baselined before consequential architecture work begins, otherwise M2 inherits an unstable foundation. Work is split into three parallel workstreams with a fixed integration point rather than sequential handover. |
| CN-03 | Cost / resources | Free or low-cost services only. Free-tier limits and likely operational cost beyond the educational context must be identified. | Rules out paid messaging gateways (CF-03), managed object storage at scale (SCOPE-D-01) and always-on compute. Directly shapes the achievable performance and availability targets and therefore the M2 architecture. |
| CN-04 | Quality | Quality attributes must be defined now and supported by measurable evidence later. Unsupported claims are not accepted. | Every NFR carries a metric and a named verification method, even where the measurement itself only becomes possible in M3. NFRs without a measurement route were rewritten or removed. |
| CN-05 | Security | Security is a lifecycle responsibility from requirements onwards, not a final hardening pass. | Authentication, authorisation, secrets handling, audit and privacy requirements are baselined in M1 so that M2 architecture cannot quietly design them out. Residual risk is recorded rather than a claim that the system is secure. |
| CN-06 | Team capability | Three students of mixed and partly unknown proficiency. Learning-curve risk must be treated as an engineering constraint. | Technology selection is deferred to M2 so it can be made against an honest capability audit and a small proof of concept rather than familiarity or preference. |
| CN-07 | Environment / platform | Belgium Campus cannot guarantee that any chosen language, framework, service or deployment platform is available or supported on the institutional desktop platform (Master Project Brief section 25). | Availability and compatibility must be verified on the actual build environment before the stack is committed in M2. A stack that only runs on one member's personal machine is a single point of failure. |
| CN-08 | Governance | Protected main, pull requests for substantive change, and a minimum of two approvals from members other than the author. Self-approval is not accepted. | With a three-person team, two approvals means unanimous consent from the other two members. Any single absence blocks every merge, so a review turnaround rule and an escalation path are required from the start. |

## 5.1 Constraint interaction — cost, quality, architecture

The interaction is where the engineering consequence lives, and this chain is why two decisions are deferred rather than taken.

| Link | Effect |
|---|---|
| CN-03 binds | Only free-tier services. Free tiers idle out and cold-start, throttle compute and cap storage. |
| → quality | NFR-001 cannot honestly promise 2 seconds on a cold instance, so it is specified against a warm instance at stated concurrency and volume; NFR-002 declares cold-start latency as a known limitation rather than concealing it. |
| → architecture | Each independently deployed service is another instance that idles out, pushing M2 towards a single deployable unit. A financial constraint becomes an architectural one — to be argued in M2, not assumed now. |
| → verification | M3 load testing must separate warm from cold measurements or the NFR-001 evidence is meaningless. |
| → evaluation | NFR-010 requires operational cost at 100 users and 1 000 requests per month — where the free-tier assumption is honestly tested. |
| Residual risk | RSK-02 (16, High). Contingency is to publish the degraded behaviour or renegotiate CN-03 — not to quietly weaken the NFR. |

A second interaction runs between CN-08 and CN-02: two approvals from non-authors means unanimity in a three-person team, so a single absence halts every controlled merge. The control cannot be weakened, so the schedule absorbs it — DEC-010 fixes a 24-hour review turnaround and RSK-04 carries the residual exposure.

## 5.2 Assumptions

| ID | Assumption | Consequence if false | Risk | Validation |
|---|---|---|---|---|
| AS-01 | The team acts as proxy for all CivicConnect stakeholders; no live client is available for validation. | Requirements may not reflect real operational practice | RSK-10 | Validate with lecturer as proxy client at the M2 gate |
| AS-02 | Provisional target resolution times per category may be set by the team and corrected later without breaching the baseline, because FR-021 is specified against a configurable value. | FR-021 acceptance testing is possible now; only the values are provisional | RSK-05 | Confirm values at the M2 gate |
| AS-03 | Email delivery is available at no cost within the free-tier limits of the platform selected in M2. | FR-009 becomes unimplementable as specified if untrue | RSK-02 | Verify during the M2 platform spike |
| AS-04 | Request volume during the academic project remains within the capacity stated in NFR-013. | Performance and cost evidence would need re-basing | RSK-02 | Re-check at M3 load testing |
| AS-05 | All three registered members remain on the team for the full delivery period. | Two-approval governance and workstream split both assume three members | RSK-04, RSK-09 | Escalate to lecturer if it fails |
