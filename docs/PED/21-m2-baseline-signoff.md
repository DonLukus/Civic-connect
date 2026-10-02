# PED §21 — M2 Baseline Sign-Off

> **PED v2.0 section, new at M2.** Owner: Emile.
> Authored here in Markdown, compiled to `docs/PED/exports/PED_v2.0.docx` at the M2 baseline (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

The full sign-off record — what is included, known limitations, open decisions and the three
signatures — lives in `docs/baseline/M2-baseline-signoff.md`, not duplicated here, in the same
way §20 references ADR-006 rather than restating it. This section narrates it for the PED's own
continuity, as §15 did for the M1 sign-off.

## 21.1 Current outcome

As of the last recorded review (30 September – 1 October 2026), the baseline's own Outcome field
reads **PROPOSED**, not ACCEPTED. All three members have signed the 30 September review; the
1 October evidence update (PoC log, PR #62, PR #63) is recorded but has not yet been separately
re-approved by all three per that file's own note under "Outcome."

Two concrete reasons this stays PROPOSED, neither hidden:

1. ADR-001 (architecture and technology stack) and ADR-007 (authentication/authorization
   placement) are both still **Proposed**, not Accepted — the evidence DEC-008 requires (a
   login/save/deploy proof of concept verified on a live host, not assumed) is not yet complete.
   See `docs/decisions/poc-log.md`.
2. The decision register itself has not caught up with the ADRs it should be logging — see the
   gap recorded in `docs/PED/00-document-control.md`'s "Linked controlled artefacts" table and
   its graduation checklist.

## 21.2 What moves this to ACCEPTED

This section and `docs/PED/00-document-control.md` update together, in one pull request, once
every condition in that document's "When v2.0 moves from Draft to BASELINED" checklist is true.
Nothing here pre-empts that review — this section currently records PROPOSED because that is what
the controlled sign-off file actually says, not because a different outcome is expected.
