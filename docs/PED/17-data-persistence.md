# PED §17 — Data Persistence

## 17.1 Purpose

This section captures the M2 persistence design for CivicConnect. It sets the authoritative persistence model for request data, audit data, and integration events, and it ties the design to the project requirements and quality constraints.

## 17.2 Data model

The core aggregate is the Request. A Request has one current state, one assignee, a version, and an immutable audit trail. The request aggregate is responsible for lifecycle legality and for tracking assignment changes.

Entities:
- User
- Request
- Category
- RequestComment
- RequestAudit
- OutboxEvent

Key fields:
- Request.id
- Request.version
- Request.status
- Request.assignee_id
- Request.requester_id
- Request.category_id
- Request.created_at, updated_at
- RequestAudit.request_id, actor_user_id, previous_status, new_status, previous_assignee_id, new_assignee_id, changed_at, correlation_id
- OutboxEvent.correlation_id, aggregate_type, aggregate_id, event_type, payload_json, state, attempts, last_error, created_at

## 17.3 Correctness rule for FR-014 and FR-025

The real concurrency control is not a UI check. It is a conditional optimistic update with version verification.

Pseudo-SQL:

```sql
UPDATE requests
SET assignee_id = :staff_id,
    status = 'Accepted',
    version = version + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :request_id
  AND assignee_id IS NULL
  AND status = 'New'
  AND version = :expected_version;
```

If rowcount = 0, then another Staff member or transaction has already changed the request. The system rejects the second acceptance. This is the actual correctness mechanism protecting FR-014/FR-025.

## 17.4 Audit and outbox consistency design

The request-change transaction must be atomic across three writes:
1. update the Request row with version increment
2. insert the immutable RequestAudit row
3. insert the outbox row with the same correlation ID

This guarantees that the domain fact and the evidence of change stay together. The outbox row is the integration boundary and the audit row is the authoritative trace.

Outbox state machine:
- pending -> sent -> failed
- failed carries attempts and last_error
- failed items may be retried without altering the request state

## 17.5 SPOF, backup and scalability notes

- There is a single primary database by default; the app tier remains stateless.
- Daily backup and periodic restore testing is required by NFR-011.
- Outbox processing is asynchronous and replayable so a notification outage does not break the business transaction.
- The design avoids a large synchronous fan-out on the request path and remains compatible with free-tier hosting constraints.

## 17.6 Decision summary

The persistence design is an adapted version of A2: relational versioned aggregate + immutable audit row + outbox. It preserves correctness, operational resilience, and project-fit for the current M2 constraints.
