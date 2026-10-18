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

## Correction from execution-log review - 18 October 2026

The earlier full-history label was not supported merely by fetch-depth: 0. Main quality run 39029611356, job 117387258105, invoked Gitleaks with `--no-merges --first-parent` and a restricted range; the log reports **0 commits scanned**. Its green result does not prove a full-history scan. This is a correction of the claim, not proof of a credential leak. Explicit history verification is pending and will be recorded separately if actually run. Required-status-check lists and stale-approval dismissal remain the settings gaps already recorded; no administrator setting was changed by this closure work.

Method reference: https://github.com/gitleaks/gitleaks - the raw git scanner's history selection depends on its log options, not only checkout depth.

### Explicit history verification obtained

Manual quality run [39090851534](https://github.com/DonLukus/Civic-connect/actions/runs/39090851534), job [117567103523](https://github.com/DonLukus/Civic-connect/actions/runs/39090851534/job/117567103523), scanned **174 commits** on application candidate `98b1c55700d940f915d856119f581adee8044986` with no leaks found, applying only the existing exact historical false-positive fingerprint. The logged command has no restricted PR/push log-opts. This is actual full-history evidence for that candidate; it does not change bypass actors, push protection or required-check settings. The earlier zero-commit result remains recorded as a corrected evidence gap.
