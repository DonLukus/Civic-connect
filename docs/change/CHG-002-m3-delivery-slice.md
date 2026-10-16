# CHG-002 - M3 delivery slice (review proposal)

Requested by: Emile, recording the scope discussion reported in the team conversation. Prepared 16 October 2026. **Formal repository approval is pending; no new student agreement is inferred.**

## Requested change and reason

Demonstrate login for all four roles, Requester submission and own request/status, Staff queue/detail/self-acceptance, and acceptance notification. Limit FR-012 to status filtering and FR-015 to New-to-Accepted. This produces two verifiable journeys within the M3 schedule while exposing the remaining baseline gaps.

Defer Manager reporting/dashboard (FR-019?022), operational Administrator account/category management (FR-023/024), later transitions (FR-016?018), password reset (FR-004), comments (FR-010) and duplicate prompting (FR-026). FR-001 is only bootstrap provisioning in this slice; it does not meet the baselined administration/self-registration criteria.

## Impact

- Requirements and priorities stay baselined; a deferred Must remains an unfulfilled obligation, not a passed requirement.
- Architecture remains the layered server-rendered candidate; ADR-001 and ADR-007 status changes need actual acceptance. DEC-008 remains Deferred.
- Existing transaction/audit/outbox schema supports the slice. Broader administration, reporting, lifecycle and historical-hash migration remain work.
- Verification is scoped: two live HTTP journeys, representative negative/role checks, separate load test. The full role matrix and remaining acceptance criteria cannot be inferred from this slice.
- Local simulated staging reduces cloud filesystem exposure during the demonstration, but does not resolve durable hosted storage, external email, uptime or production capacity.
- Residual risks and technical debt are indexed in the release summary and technical debt register. No paid service is introduced.

## Decision requested

Recommend accept the delivery slice for M3 evaluation with explicit exclusions, subject to the assessment brief and team review. Don and Masego must record their actual decision/date through review. Until then this is a review proposal; it does not amend the approved product baseline or establish release readiness.
