# ADR-002: Persistence

- Status: Accepted
- Date: 2026-09-30
- Deciders: Don, Masego, Emile

## Context

FR-009 requires request-state notifications to the requester, FR-014 requires controlled assignment/acceptance, FR-015..FR-018 constrain lifecycle legality, and FR-025 imposes immutable auditability. The system must also preserve request history and remain recoverable under NFR-011. This cannot be implemented by a single “last write wins” model because acceptance races and status changes are business-critical.

The project baseline also requires a single source of truth and a recoverable data store (CN-03, CN-05, NFR-006, NFR-011). The project is intentionally early in M2 and cannot yet commit to a full deployment platform, so the persistence decision must remain platform-agnostic but correct in principle.

## Constraints

- CN-03: cost and free-tier constraints are real
- CN-05: security and traceability must be enforced
- NFR-006: status and assignment changes must be auditable
- NFR-011: daily backup and restore test required
- FR-014 / FR-025: status and assignment changes must be attributable and not silently overwritten

## Alternatives considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| A | Simple single-table request record with direct updates | Easy to implement | No concurrency protection, weak auditability, poor separation of read/write effects |
| B | Versioned request table + immutable audit table + outbox for notifications | Correct concurrency semantics, auditable, supports async fan-out | Requires careful transaction boundaries |
| C | Event-sourcing ledger only | Excellent auditability | Too heavy for project scope and team size |

## Decision

Adopt a versioned request aggregate with immutable audit rows and an outbox for notification fan-out. The persistence layer will keep the authoritative request state in a relational table, add optimistic concurrency using a `version` column, persist every business change to an immutable audit table, and emit domain events through an outbox row.

## Rationale

This is the correct adaptation of A2's service-transaction comparison. A2's comparison is a good starting point, but the project's real requirements are stricter: a request must not be accepted twice by different Staff users, and every status/assignment change must retain who changed it and what changed. A versioned aggregate plus immutable audit rows provides both correctness and traceability while remaining implementable within the project's M2 time box.

## Trade-offs accepted

- Extra writes per state change (audit row and outbox row)
- More code and a stricter transaction boundary
- Async notifications require retries and monitoring

## Risks created

- RSK-08: operational failure of notification services not blocking the business change
- RSK-02: platform failure or restore challenge during a live incident

## Evidence

- FR-014, FR-015, FR-025, NFR-006, NFR-011
- Current repo baseline and RTM for persistence-related requirements
- POC spike findings: same-transaction audit + optimistic update is required to prevent double acceptance

## Downstream consequences

- Every request change must use the same transaction pattern.
- Notification logic must be async and retryable to avoid blocking business state changes.
- Deployment must include backup/restore procedure and monitoring for outbox processing.

## Later consequence (updated when evidence emerges)

Left blank at decision time.
