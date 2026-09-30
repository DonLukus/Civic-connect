# ADR-003: Design Pattern — Lifecycle Validator

- Status: Accepted
- Date: 2026-09-30
- Deciders: Don, Masego, Emile

## Context

FR-015 defines a finite lifecycle for requests across New, Accepted, In Progress, On Hold, Resolved, Closed and Rejected. FR-016, FR-017 and FR-018 add role- and reason-based constraints. The actual system must refuse illegal transitions. The requirement is not merely a theoretical state machine; it is an operational safety rule.

A2 offered a comparison between transition-table validation and State pattern. For CivicConnect, the lifecycle rules are explicit and finite, and the project team needs straightforward auditability and testability.

## Constraints

- FR-015: only defined transitions are allowed
- FR-016 / FR-017 / FR-018: actions and reasons must be valid for the transition
- FR-025: the transition must be traceable in audit records
- NFR-004: rejection of unauthorised role changes must be enforced without state mutation

## Alternatives considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| A | Transition-table validator in the service layer | Simple, explicit, auditable, easy to test | More boilerplate than a pure state object |
| B | State pattern with per-state handlers | Polymorphic and extensible | More indirection, harder to audit and validate in review |
| C | No explicit validation; rely on UI rules only | Fast to prototype | Fails requirements and auditability; unsafe |

## Decision

Use a transition-table validator as the primary lifecycle enforcement mechanism, with a normalised request state enum and explicit allowed transitions checked inside the domain service before writing any state change.

## Rationale

The lifecycle is a business policy table, not a general object state problem. The project team needs a clear rule set, reviewable in code and tests, and not an over-engineered hierarchy. For CivicConnect, the transition table is the right design because it makes the requirement visible and verifiable.

The State pattern remains a possible future refactor if the lifecycle becomes much richer, but it is not the primary fit for the current requirement set.

## Trade-offs accepted

- A table requires disciplined maintenance when rules change
- The service layer carries more validation logic than a pure OOP state model would

## Risks created

- RSK-02: wrong transition table can silently block valid work
- RSK-08: flawed rules can create user confusion and operational support load

## Evidence

- FR-015, FR-016, FR-017, FR-018
- PED lifecycle states definition in docs/PED/06-requirements.md
- Project requirement traceability from RTM
- **Implementation**: `src/persistence/lifecycle.py::LifecycleValidator`, extracted from the
  inline check previously in `RequestService.accept_request`. Deliberately partial — only the
  New→Accepted transition (FR-014, CHG-001) is encoded, because it is the only one the requirement
  set currently specifies concretely; encoding the rest of FR-015's table without an approved
  specification would be inventing business rules, not implementing them. Tested in
  `tests/test_lifecycle_validator.py` (3 tests) and exercised indirectly by
  `tests/test_request_acceptance.py`.

## Downstream consequences

- Every lifecycle change must pass through the same validator.
- Audit rows must reflect the actual transition rather than an ad hoc “status field only” assignment.
- New transitions require test updates and a rules review.

## Later consequence (updated when evidence emerges)

Left blank at decision time.
