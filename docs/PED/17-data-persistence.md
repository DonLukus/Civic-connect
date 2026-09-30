# ADR-006: Integration Decision

- Status: Accepted
- Date: 2026-09-30
- Deciders: Don, Masego, Emile

## Context

The project must integrate request state updates, audit records, and notification delivery without losing correctness or auditability. A2 provided a four-way integration comparison; the project currently needs a practical pattern adequate for a small team and free-tier hosting constraints.

The decision must explicitly answer the rollback question: if a downstream notification or integration event fails, does the request state rollback? The answer must be no for the domain fact, yes only for the message send attempt if the send is still in the same local transaction.

## Constraints

- CN-03: low-cost, free-tier constraints
- NFR-011: backup and recoverability
- FR-009 / FR-025: audit and notifications must remain accurate
- NFR-004: unauthorised state changes are blocked without state mutation

## Alternatives considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| A | Synchronous HTTP integration | Easy to reason about initially | Couples services, poor resilience, blocks business transaction |
| B | Message queue with direct publisher | Better decoupling | Requires operational message broker and monitoring |
| C | Outbox-based async integration | Correct audit boundaries, resilient, low operational complexity | More moving parts than synchronous calls |
| D | Do nothing; keep everything local | Simplest | Fails FR-009 and auditability under operational failure |

## Decision

Use an outbox-based asynchronous integration model. The request service writes the business change and audit row in one transaction, then emits an outbox row with a shared correlation ID. A separate process publishes the event and moves the outbox row from pending to sent or failed with an attempt count.

## Rationale

This is the best fit for a small team and low-cost project. It preserves core business correctness, avoids blocking UI operations on third-party services, and supports retry semantics without undoing the business fact. This is the correct adaptation of A2's four-way comparison for CivicConnect.

## Trade-offs accepted

- Event processing is eventually consistent
- Some notifications may be delayed during outages
- Monitoring and retry logic are required

## Risks created

- RSK-08: downstream service outage may delay notifications
- RSK-02: infrastructure failure at the app or DB layer can affect event emission

## Evidence

- FR-009, FR-025, NFR-011
- Persistence ADR and notification ADR
- Architecture decision requirement for explicit rollback semantics

## Downstream consequences

- Every business state change must have a correlation ID and an outbox row.
- Notification failures are retried or marked as failed; they do not revert the request lifecycle state.
- The deployment model must include monitoring of the outbox worker and backup/restore tests.

## Later consequence (updated when evidence emerges)

Left blank at decision time.
