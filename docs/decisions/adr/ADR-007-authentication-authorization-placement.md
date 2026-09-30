# ADR-007: Authentication and Authorization Placement

- **Status:** Proposed
- **Date:** 2026-09-30
- **Deciders:** Masego (proposed); Emile (raised the gap as RSK-16 and proposed this direction
  during ADR-001 review); still needs Don

## Context

ADR-001 resolved the frontend, backend, database, testing and CI layers but never placed
authentication or authorization architecturally, even though NFR-004 and NFR-012 are named
architecturally significant requirements in PR #27's ASR set. The traced slice
(`src/web/app.py`) currently runs against a hardcoded stand-in (`REQUESTER_ID = 1`), disclosed in
the code and the README, not hidden — but nothing decides what replaces it. Emile's review of
ADR-001 recorded this gap as **RSK-16** and proposed the direction this ADR formalises: service-layer
enforcement, consistent with where ADR-002's transaction boundary and ADR-003's transition guard
already live, rather than per-view checks.

This ADR decides *where authorization logic lives* and *what identity mechanism the traced slice
needs next*. It does not build FR-001..FR-004 (the full login feature) — that is a separate,
subsequent slice. Deciding placement now, before that slice is built, is exactly what FEC-04
warned about: retrofitting access control after features exist means re-touching every endpoint.

## Constraints

- **NFR-004** — unauthorised state changes must be blocked without state mutation (the check must
  happen before any write, not as an audit-after-the-fact).
- **NFR-012** — restricts who can see a requester's details to the assigned staff member, the
  manager and the administrator — a **per-record**, not per-route, decision (CF-01, DEC-006).
- **CN-05** — security is a lifecycle responsibility from requirements onward, not a final
  hardening pass.
- **CN-03** — no additional paid service (rules out an external identity provider as the default).

## Alternatives considered

| Option | Description | Pros | Cons |
|---|---|---|---|
| A | Per-route decorators (e.g. Flask `@login_required` / `@role_required` on each view function) | Familiar, fast to add, visible at the route | Checks the route, not the data — cannot express NFR-012's per-record "only the assigned staff member" rule; a direct internal call to the service (e.g. from the future outbox worker or a test) bypasses it entirely, since the check never reaches the domain logic |
| B | Global middleware / `before_request` hook only | One place to enforce login | Coarse — same limitation as A for per-record authorization, and cannot vary by operation |
| C | Service-layer enforcement — the domain service receives the acting user/role and checks authorization as part of the same transaction that writes the change | Matches where every other correctness rule already lives (ADR-002's transaction, ADR-003's transition guard); cannot be bypassed by an internal caller, because the check is inside the thing being protected, not in front of it; naturally expresses NFR-012's per-record rule, since the service already loads the record it is checking | The route layer must still extract *identity* (who is logged in) even though it delegates *authorization* (what they may do) to the service — two concerns, not one, need to be named explicitly or reviewers will conflate them |

## Decision

**Option C.** Identity is established at the route layer (a session cookie via Flask's built-in
session, not a new dependency — DEC-006 requires authenticated submission, not a specific
provider). Every domain-service method that changes state or returns another user's data accepts
the acting user's id and role as an explicit parameter — the same shape `accept_request(request_id,
staff_id, expected_version)` already uses — and checks authorization against the record it loads,
before writing anything, mirroring `LifecycleValidator`'s placement in ADR-003.

## Rationale

`RequestService.accept_request` and `create_request` already pass the acting user's id as an
explicit argument, not through a global session lookup inside the service — this ADR generalises
a pattern already present rather than introducing a new one. It is also the only option that can
express NFR-012's per-record rule at all: "can this Staff user see this Requester's details"
depends on whether they are the assigned staff member for *that specific request*, information a
decorator or middleware cannot see without loading the record — which means it would end up
calling into the service anyway, just less honestly.

## Trade-offs accepted

- Every future service method needs an explicit acting-user parameter and an authorization check
  inside it — more boilerplate per method than a single decorator line, accepted because the
  alternative cannot satisfy NFR-012.
- The route layer still needs *some* login/session mechanism (identity), so this ADR does not
  remove the need to build FR-001..FR-004 — it only decides where the *authorization* half of the
  work goes once that identity exists.

## Risks created

- **RSK-16** (this ADR's own subject) moves from "undecided" to "placement decided, not yet
  implemented" — it stays open on the risk register until FR-001..FR-004 and the corresponding
  service-layer checks actually exist.
- No new risk beyond RSK-16 itself; this ADR is scoped to placement, not implementation.

## Evidence

- RSK-16 (Emile, ADR-001 review, PR #41).
- NFR-004, NFR-012 — PR #27's ASR table.
- FEC-04 — security architecture must exist before construction, not after.
- The existing parameter shape of `RequestService.accept_request` and `create_request`, both
  already passing an acting-user id explicitly.

## Downstream consequences

- The next role-differentiated slice (FR-014's staff/manager distinction, or FR-002/FR-003 login
  itself) must add the acting-user parameter and an authorization check to any new or existing
  service method it touches, not defer it further.
- `src/web/app.py`'s `REQUESTER_ID = 1` stand-in must be replaced by a real session-derived id once
  FR-001/FR-002 exist — this ADR does not build that, it decides where the check goes once it does.
- RTM rows for NFR-004 and NFR-012 should move from "Pending M2" to "Design decided, implementation
  pending" once this ADR is accepted (not yet done here — see RTM update in this same change).

## Later consequence (updated when evidence emerges)

Left blank at decision time.
