# M3 staging environment

Owner: Emile. Builds on `deployment-direction.md` (Masego, M2) rather than restating it — read
that file first for the hosting/configuration/networking direction this inherits.

## Status

**Environment choice not yet agreed with Don.** The M3 brief allows a credible local/simulated
environment instead of cloud deployment — that decision needs to happen between us, not be
assumed here. This document records the plan and what each choice implies; it does not pick one
unilaterally.

| Option | What it would mean |
|---|---|
| Render (continuing from M2) | Reuses the existing service; M2's unresolved persistence-after-redeploy problem (`docs/decisions/poc-log.md`) would need to be understood or worked around before trusting any M3 result on it |
| Local/simulated (e.g. a second SQLite file, run via Flask's dev server or gunicorn where available) | Avoids the unresolved Render persistence question entirely, but needs to be run on a machine that can actually install the full `requirements.txt` — not this one; see the performance README for the same local-Python gap |

## Configuration and secrets (inherits the M2 approach)

Environment variables only, `.env.example` names them without values, nothing committed — same
as `deployment-direction.md` already states and `secret-scan.yml` already enforces. Test accounts
for the M3 journeys (Requester, Staff, and the Manager/Administrator landing page) are provisioned
the same way the existing login PoC provisions its one throwaway account
(`BOOTSTRAP_REQUESTER_EMAIL`/`PASSWORD`-style env vars) — exact variable names to be agreed with
Don once the real routes exist, documented here once they do. Credentials themselves are shared
with the team privately (not in this repo, not in any PR), per the project's existing secret
discipline.

## Startup and deployed-commit tracking

Whatever environment is agreed, every staging run records: the exact commit SHA deployed, the
startup command used, and anything that differs from a developer's local setup (e.g. gunicorn
vs. Flask's dev server) — same discipline `poc-log.md` already uses for the M2 evidence, extended
here rather than duplicated.

## Persistence / restart behaviour

To be tested once the environment is agreed, explicitly distinguishing:
- a **local process restart** (stop/start the same Flask or gunicorn process) — M2 already has
  one real result for this (survived, on the BC desktop, per `poc-log.md`'s 5 October entry).
- a **cloud redeploy** (a new container/instance entirely) — M2's one real result for this is
  negative (a submitted request was unavailable after a Render redeploy). If M3 stays on Render,
  this needs re-investigating, not re-asserting; it is not safe to assume the same or a different
  outcome without actually testing it on the current M3 commit.

## Rollback / recovery procedure (draft — to confirm against whichever environment is chosen)

1. Identify the last known-good deployed commit SHA (recorded per run, above).
2. Redeploy that commit specifically, not just "the previous version" from memory.
3. **Data implication to state plainly, not assume:** if the environment turns out not to
   persist data across a redeploy (see above), rolling back the code does **not** roll back to
   any particular data state — there may be none to roll back to. If the environment does persist
   data on a real database (e.g. a hosted Postgres, not yet chosen per DEC-008), rollback of code
   without a matching database migration rollback could leave schema and code mismatched — this
   procedure gets filled in with the real mechanism once the production database decision
   (DEC-008) is actually made, not before.
4. Record what was rolled back, when, and why in `docs/governance/ai-usage-register.csv` if AI
   assisted in diagnosing the need for rollback, and in the project history otherwise.

## Still needed before this document is more than a plan

- Don: agree the environment (table above).
- Masego: confirm which M3 journeys get verified on the deployed candidate, and when, so staging
  readiness and verification readiness land together rather than one blocking the other.
- A real run, with a real result, replacing each "to be tested" above.
