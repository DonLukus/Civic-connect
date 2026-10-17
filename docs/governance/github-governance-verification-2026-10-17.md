# GitHub governance verification, 2026-10-17

Purpose: record what the repository actually enforces, against `PROJECT_RULES.md` section 10 and DEC-001.
Method: unauthenticated GitHub REST API reads on a public repository (`/rules/branches/main`, `/rulesets`,
`/pulls`, `/pulls/{n}/reviews`, `/commits/{sha}/check-runs`). Unauthenticated reads cannot show bypass
actors, secret-scanning settings or the legacy branch-protection page, so those are **not verified** and
need a repository admin to export or screenshot them.

## Enforced on `main` (two active rulesets, created 2026-10-01)

| Rule | Documented | Actual |
|---|---|---|
| Pull request required | On | On |
| Required approvals | 2 | 2 |
| Approval of the most recent push | not stated | On |
| Conversation resolution | On | On |
| Block force push | On | On |
| Block deletion | On | On |
| Dismiss stale approvals on new commits | **On** | **Off** (`dismiss_stale_reviews_on_push: false`) |
| Code-owner review | not stated | Off, so `CODEOWNERS` is advisory |
| Required status checks | implied by M3 DoD | **None.** Both rulesets list an empty `required_status_checks` |
| Bypass actors | "do not allow bypass" On | **Not verifiable** without admin access |
| Secret scanning + push protection | On | **Not verifiable** without admin access |

Consequence: a failing CI run does not block a merge today. "Last-push approval" partly offsets the missing
stale-approval dismissal, but it is not the documented control.

## Historical approvals (42 newest merged PRs, #22 to #90)

"Approved" counts distinct non-author reviewers whose review state is APPROVED. The 9 oldest merged PRs were
not checked (API rate limit).

- 35 of 42 had at least 2 non-author approvals.
- One approval only: #22, #26, #28 (all 2026-09-30, before the rulesets existed).
- No approvals: #54, #55, #56 (2026-09-30, before the rulesets) and **#75 (2026-10-05, after the rulesets
  existed)**. How #75 merged is unexplained; a ruleset bypass or an admin override are the candidates and
  neither can be confirmed here.
- Independence caveat: one student appears under two GitHub accounts (`DonLukus`, `Don-Sanvura`). Approval by
  one account on the other's PR is not independent review. This was not audited PR by PR.

The documented claim that every merged PR carried two independent approvals is therefore **not supported**
for the PRs above and is recorded as a discrepancy, not as a pass.

## CI on the latest `main` commit (6e99ae6)

All four check runs concluded `success`: `tests-and-static-analysis`, `secret-scan` (gitleaks, full history),
`traceability`, `scan` (pattern grep). No CodeQL workflow exists in the repository.

## Actions required (need agreement and admin rights; not applied by this change)

1. Turn on dismiss-stale-approvals; decide on code-owner review.
2. Add `tests-and-static-analysis`, `secret-scan` and `traceability` as required status checks.
3. Admin to export the ruleset JSON and bypass list, and the secret-scanning settings page, into
   `docs/governance/evidence/`.
4. Explain PR #75 and record the answer here.
5. Attempt a direct push to `main` and a self-approval from a non-admin account; keep the refusals as evidence.
