# M2 Architecture, Technology & Initial Design Baseline Sign-Off

Per Master Project Brief Appendix D and the M2 brief §6. This does **not** claim the detailed
design is finished — per the brief's own wording, it records that the team has enough controlled
direction to develop without repeatedly making foundational decisions ad hoc.

| Field | Record |
|---|---|
| Project | CivicConnect — Community Service Request Management Platform |
| Baseline type | Architecture, Technology & Initial Design Baseline |
| Version | PED v2.0 (in progress — see `docs/PED/00-document-control.md`) |
| Date | 2026-09-30 |

## What is included in this baseline

- **Architecture style**: single deployable unit (ADR-001, Proposed), justified against the M1
  cost-chain conclusion in PED §5.1 rather than assumed.
- **Persistence pattern**: versioned aggregate + immutable audit table + outbox (ADR-002,
  Accepted).
- **Two design-pattern decisions** (M2 brief §5.6, both Accepted): transition-table lifecycle
  validator (ADR-003) and observer-style notification fan-out via the outbox (ADR-004).
- **Integration pattern**: outbox-based async integration, explicit on the rollback question
  (ADR-006, `docs/decisions/adr/ADR-006-integration-decision.md`).
- **Technology stack direction** (ADR-001, Proposed): Python 3.11 + Flask 3.1.3, SQLite for
  dev/test, PostgreSQL as the production candidate, pytest, GitHub Actions — versions verified
  against PyPI's published metadata, not asserted (`docs/decisions/technology-versions.md`).
- **Traced feature slice**: "Citizen submits a service request" (FR-005, FR-006) built end to
  end — `src/web/`, `RequestService.create_request`, 6 passing tests — the evidence this baseline
  is not aspirational.
- **Deployment direction** (Proposed): `docs/deployment/deployment-direction.md`.
- **Architecture diagram**: `docs/decisions/adr/ADR-001-architecture-and-stack-options.md`
  (logical layers vs. physical deployment, explicitly distinguished per brief §5.3).

## Known limitations of this baseline

Recorded deliberately, per the M1 sign-off's own precedent — stating a limitation scores better
than an unsupported claim of completeness.

1. **ADR-001 is Proposed, not Accepted.** DEC-008 still requires a proof-of-concept — login,
   save, deploy — run on the actual Belgium Campus platform, per CN-07. Nothing above is final
   until that evidence exists.
2. **Authentication and authorization architecture is undecided** (RSK-16, opened during Emile's
   review of ADR-001). The traced slice runs against a hardcoded stand-in requester, disclosed in
   the code and the README, not hidden. This must be resolved before the next role-differentiated
   slice (FR-014) is built against an unreviewed assumption.
3. ~~ADR-003's transition-table validator has no extracted implementation~~ — **fixed in this
   same baseline**: `src/persistence/lifecycle.py::LifecycleValidator` now holds the New→Accepted
   rule as an explicit, tested, reusable check. Still partial by design: only the one transition
   the requirement set actually specifies (FR-014/CHG-001) is encoded — the rest of FR-015's
   seven-state table has no approved specification yet, and inventing it would not be
   implementing a decision, it would be making one nobody reviewed.
4. **SQLite vs. PostgreSQL for production is unverified.** ADR-001 recommends SQLite for dev/test
   only, on the reasoning that it is a SPOF risk in a real hosted deployment — this has not been
   tested under an actual deployment attempt.
5. ~~A file/content numbering mismatch existed in `docs/PED/`~~ — **fixed in this same
   baseline**: `17-data-persistence.md`, `19-design-decisions.md` and
   `20-integration-deployment.md` each held content whose own heading named a different section
   number than the filename, and a fourth document (`ADR-006: Integration Decision`) had been
   filed as a PED section instead of an ADR. Rotated to the correct filenames and extracted
   ADR-006 to `docs/decisions/adr/`; §20 rewritten to reference it rather than duplicate it.
6. **The RTM is only fully evolved for the traced slice.** `TR-001` (FR-005), `TR-004` (FR-009),
   `TR-011` (FR-014) and `TR-013` (FR-006) carry M2 evidence; the remaining 36 rows still read
   Pending M2, which is the brief's own acceptable controlled status for evidence that does not
   yet exist — not a gap to hide.

## Open decisions, deliberately deferred

| Decision | Evidence still required |
|---|---|
| DEC-008 (stack/architecture/hosting, formally Deferred in the decision log) | Belgium Campus platform PoC — login, save, deploy |
| Authentication/authorization placement (RSK-16) | An ADR-001 addition or its own short ADR, before the next role-restricted slice |
| SQLite vs. PostgreSQL for production | An actual deployment attempt against both |
| M2 team-lettering (Member A/B/C mapping in `docs/PED/00-document-control.md`, PR #22) | Confirmation against the actual M2 assessment brief's criteria text — flagged, not resolved unilaterally |

## Outcome

**PROPOSED** — sufficient controlled direction exists to continue development (the traced slice
is the evidence), but the baseline is not yet **ACCEPTED** because ADR-001 itself is Proposed and
RSK-16 is unresolved. Re-run this sign-off once the DEC-008 PoC evidence lands.

## Signatures

| Member | M2 role (proposed, PR #22 pending confirmation) | Signature | Date |
|---|---|---|---|
| Masego | Technology and delivery | [ ✓ ] | 2026-09-30 |
| Don | Data and design patterns | [ ] pending | |
| Emile | Architecture and requirements | [ ] pending | |
