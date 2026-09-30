# PED §19 — Design Decisions

## 19.1 Lifecycle decision

The lifecycle problem is the real status-transition problem, not merely a UI state. FR-015..FR-018 constrain the legal movement of request status, and the same rules must be enforced in the domain service as well as in the UI.

Decision: use a transition-table validator rather than a pure State pattern.

Reason:
- the rules are finite and explicit
- the project needs easy review and tests
- the legal transitions can be expressed in a table and enforced in a single validation step

## 19.2 Notification and audit fan-out decision

FR-009 and FR-025 require both requester communication and immutable auditability.

Decision: use observer-style fan-out, but do not roll back the status change when a notifier fails.

Reason:
- the request state is the business fact
- notification is a downstream delivery concern
- email or in-app channel outages must not erase a valid lifecycle change

The failure handling is therefore:
- change is committed
- audit row is committed
- outbox event is inserted as pending
- notification is retried or marked failed

## 19.3 Persistence decision summary

The persistence layer uses a versioned aggregate plus immutable audit and outbox.

This is an adapted A2 solution with direct application to the current requirement set.
