# Architecture Baseline

> **PED v2.0 section, new at M2.** Owner: Emile.
> Authored here in Markdown, compiled to `docs/PED/exports/PED_v2.0.docx` at the M2 baseline (DEC-002).
> The compiled document is an output — never edit it directly, and never treat it as the source of truth.

## 16.1 M1 baseline review

Before adding any M2 decision, the whole M1 baseline (`docs/PED/01`–`15`, the decision log, the risk, requirements, scope and stakeholder registers) was read through end to end, as the M2 brief requires (§5.1). This is what that review found.

**Materially changed:**

- FR-009 and FR-014's acceptance criteria were clarified via CHG-001 — see `docs/PED/10-decision-log.md` §10.3. Both readings had already been agreed by the whole team in Assignment 2 but had never been written back into the baselined requirement text. Closed before the status-lifecycle and notification design decisions get built on top of the ambiguity.

**Still open, not actioned here — needs input the team doesn't control:**

- AS-01 and AS-02 both call for validating assumptions with the lecturer as proxy stakeholder "at the M2 gate" — target resolution-time values (FR-021, under RSK-05) and general requirement validity. That's a real conversation with the lecturer, not something resolvable by editing a document, so it stays open on the assumption register rather than being marked done.

**Everything else: reviewed, unchanged, still holds.** Identifiers are consistent across every register. DEC-001 through DEC-012 (except DEC-008, addressed below) still reflect the team's actual position — nothing in Assignment 2, Assignment 3 or the M2 brief surfaced a reason to revisit any of them. The scope baseline, risk register, stakeholder register and constraints are all still accurate as written. The Forward Engineering Considerations (`09-forward-engineering.md`) already name M2 as the milestone where FEC-01 through FEC-07 get acted on — that's expected, not a gap; this file and `17`–`20` are where that happens.

## 16.2 Architecture decision

ADR-001 remains Proposed and DEC-008 remains Deferred. The original request slice passed 10 tests on the Belgium Campus desktop on 30 September 2026. On 5 October, a fresh BC Desktop checkout passed 15 tests on Python 3.14.5; a later repeat installed `requirements.txt` successfully and again passed all 15 tests in 5.88 seconds on commit `6beeb7a1353fdfdf8a9ed6966e1028b7fd3e0d75` (matching `HEAD` and `origin/main`). A disposable local request remained available after a Flask process restart using local SQLite. The login/save slice was also exercised on Render after PR #71: a test request was submitted successfully, but its confirmation route returned 404 after a successful manual redeploy. The cause is unknown, and the BC local-file result does not explain the Render result. These observations are recorded in `docs/decisions/poc-log.md`; they narrow some uncertainty but do not complete the candidate-platform comparison, capability audit or persistence investigation needed for DEC-008. ADR-001 remains Proposed, not Accepted.
