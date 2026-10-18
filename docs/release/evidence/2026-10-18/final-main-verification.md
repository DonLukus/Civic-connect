# Verification of the exact `main` commit, 18 October 2026

Commit: `73603845b0f48ccc2c65f7d13c594e0ebf1e3462` (merge of PR #103). Queried from the GitHub API and recomputed from `docs/requirements/RTM.csv` at that commit. This records facts for the final submission; it is not an approval or a signature.

## Checks on the exact commit (not the PR head)

| Workflow | Event | Result | Run |
|---|---|---|---|
| Quality gates | push | success | https://github.com/DonLukus/Civic-connect/actions/runs/39132700126 |
| Secret scan | push | success | https://github.com/DonLukus/Civic-connect/actions/runs/39132700161 |
| Static code quality (ruff) | push | success | https://github.com/DonLukus/Civic-connect/actions/runs/39132700167 |
| Tests | push | success | https://github.com/DonLukus/Civic-connect/actions/runs/39132700181 |
| Traceability check | push | success | https://github.com/DonLukus/Civic-connect/actions/runs/39132700180 |

Individual check runs attached to the commit: ai-register (success), lint (success), scan (success), secret-scan (success), test (success), tests-and-static-analysis (success), traceability (success).

## RTM re-count at this commit

- 40 rows: **12 Met, 14 Partially Met, 14 Not Met**; 19 points / 40 = **47.50%** (Met = 1, Partially Met = 0.5, Not Met = 0). This matches the verification report; the target is 80%.
- Must-priority rows assessed Not Met (9): TR-005 (FR-019); TR-006 (FR-021); TR-014 (FR-020); TR-019 (NFR-010); TR-021 (FR-023); TR-022 (FR-024); TR-024 (FR-016); TR-026 (FR-001); TR-030 (FR-017).
- Other Not Met rows (5): TR-023 (FR-010, Should); TR-028 (FR-004, Should); TR-031 (FR-018, Should); TR-033 (NFR-002, Should); TR-039 (NFR-013, Should).

## Release tag

Tag `v4.0.0` was created on 2026-10-18 as an annotated tag on `73603845b0f48ccc2c65f7d13c594e0ebf1e3462` and pushed. It was verified through the GitHub API: `refs/tags/v4.0.0` is a tag object whose target commit is exactly that full SHA. Before it was created, GitHub returned 404 for the tag.

## Limits

- Test counts belong to the PR #103 candidate (96 tests, Python 3.12.14) and are not re-executed here; the five workflows above are the checks run on the merge commit itself.
- The 47.50% is the proposed QA assessment in the RTM. It is not signed acceptance, and it does not include any work that is not on `main`.
