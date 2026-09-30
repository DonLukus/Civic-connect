# ADR-004: Design Pattern — Observer Notifications

- Status: Accepted
- Date: 2026-09-30
- Deciders: Don, Masego, Emile

## Context

FR-009 requires that a Requester is notified in-app and by email when the request is accepted, rejected, updated with a comment, or completed. The notification side effect is real but secondary to the request-domain change. The design choice is not whether notifications happen, but whether a notification failure can undo the real business event.

A2 compared Observer versus Strategy-list. The project needs a notification fan-out mechanism that is decoupled from the business rules but does not compromise domain integrity.

## Constraints

- FR-009: notify requester on key lifecycle changes
- FR-025: audit trail must remain correct even if downstream integrations fail
- NFR-006: every business state change must be attributable and immutable
- CN-05: avoid exposing data or creating fragile dependencies

## Alternatives considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| A | Observer-style notification fan-out after domain change | Decoupled, extensible, easy to add in-app + email | Requires retry and failure policy |
| B | Strategy-list with explicit notifier list | Simple for few channels | Less extensible and less decoupled |
| C | Roll back state change on notification failure | Keeps everything atomic | Violates business reality and auditability |

## Decision

Use an observer-style notification fan-out, but do not roll back the request status change when a notifier fails. The business change is committed and audited; email/in-app notification is an asynchronous side effect processed through an outbox.

## Rationale

A failed email notifier must not undo the status change. The request state is the business truth; the notification is an operational delivery concern. If the mail server is unavailable, the domain fact remains valid, auditable, and visible to a later retry.

This is aligned with the outbox pattern and the project's accountability requirements.

## Trade-offs accepted

- A user may see the status change before the email is delivered
- Notification system must include retry and dead-letter tracking
- Some notification delivery may be delayed or fail permanently

## Risks created

- RSK-08: notification infrastructure failure creates communication gaps
- RSK-02: system operational health depends on asynchronous processing reliability

## Evidence

- FR-009, FR-025, NFR-006
- Current requirement baseline and auditability practice
- Outbox pattern required by persistence ADR

## Downstream consequences

- A request change must always be recorded before notification dispatch is attempted.
- Notification processing is retriable and must not mutate the request state directly.
- The system must log failed delivery attempts and maintain a correlation ID.

## Later consequence (updated when evidence emerges)

Left blank at decision time.
