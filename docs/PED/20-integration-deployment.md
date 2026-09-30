# PED §20 — Integration and Deployment

## 20.1 Integration decision

Request state changes, audit records and notification delivery must integrate without losing
correctness or auditability (FR-009, FR-025), under the free-tier cost constraint (CN-03). The
full alternatives-considered analysis, rationale and consequences are recorded in
**ADR-006** (`docs/decisions/adr/ADR-006-integration-decision.md`), not duplicated here per the
M2 brief's instruction to reference decision evidence rather than restate it.

Summary: outbox-based asynchronous integration. The domain service writes the business change,
its audit row and a pending outbox row in one local transaction; a separate process (currently
`OutboxProcessor`, manually invoked — no scheduler yet, see the deployment direction below)
publishes the event and marks it sent or failed. A downstream notification failure never rolls
back the business fact — only the message-send attempt is retried.

## 20.2 Deployment direction

The current deployment direction — where the deployable unit runs, configuration and secrets
handling, where state lives, and networking — is recorded in
`docs/deployment/deployment-direction.md` and is **Proposed**, gated on the DEC-008
proof-of-concept, consistent with ADR-001. Deliberately deferred deployment decisions and the
evidence still required are listed there rather than assumed here.

## 20.3 What is not yet established

- No scheduler for the outbox worker (§20.1) — invoked manually today.
- No verified hosting provider (§20.2) — SQLite vs. PostgreSQL for production is an open
  question, not a decision (see `docs/decisions/technology-versions.md` and RSK-15).
- No authentication/authorization boundary sits in front of any endpoint yet (RSK-16) — this is a
  forward engineering consideration for the next slice, not silently assumed solved.
