# Final verification of release v4.0.1, 18 October 2026

Run by an AI assistant (Claude) in an isolated sandbox at the team's request, on a fresh clone of tag `v4.0.1`
(`8602ab541294f9adca09bb073a7b9cedd798689e`, the merge of PR #110). It is **not** a student's personal test
execution and not an independent acceptance. Loopback HTTP, synthetic data, Python 3.12, a fresh temporary
SQLite database.

## Results

| Check | Result |
|---|---|
| Full test suite | 293 passed |
| Persistence line coverage | 91% (1,010 statements, 93 missed); gate is 70% |
| Ruff | all checks passed |
| Bandit `-ll` (the CI command) | exit 0 |
| pip-audit | no known vulnerabilities |
| gitleaks 8.30.1, full history | 213 commits, no leaks found |

On the previous main commit (`e7ecc66`) Bandit `-ll` exited 1 with seven Medium B608 findings. Each is a false
positive: only code-defined constants or a whitelisted `ORDER BY` are interpolated and every value is bound with
`?`. PR #110 documented each with a `# nosec B608` and a reason; this verification confirms the gate now passes.
Without the repository's ignore file a raw secret scan reports 7 findings: six are the made-up test password in one
reset-route test (now marked `gitleaks:allow`) and one is a commit hash mistaken for a key.

## One live journey over real HTTP

| Step | Status |
|---|---|
| Requester, Staff, Manager, Administrator sign in | 302 |
| Requester submits a request (reference #1) | 302 |
| Staff tries to assign | 403 |
| Manager assigns to Staff (New to Accepted) | 302 |
| Staff starts work (In Progress) | 302 |
| Staff resolves without a note | 400 (refused) |
| Staff resolves with a note | 302 |
| Staff tries to close | 403 |
| Close with a stale version | 409 |
| Manager closes | 302 |
| Manager dashboard / CSV export | 200 / 200 (1 data row plus header) |
| Requester opens the dashboard; Staff opens administration | 403 / 403 |
| Administrator opens user administration | 200 |

Database afterwards: the request is `Closed`; five audit rows in order (`request_submitted`, `assign_request`, and
three `change_status` rows for In Progress, Resolved and Closed); two outbox events (`RequestAccepted`,
`RequestResolved`, pending because the worker is off by default); an `UPDATE` and a `DELETE` on `request_audit` are
both refused by the append-only triggers.

## Re-assessment against the original acceptance criteria

Scored from the 40 criteria in `docs/requirements/RTM.csv`: **28 Met, 9 Partially Met, 3 Not Met = 32.5 / 40 =
81.25%** (Met 1, Partially Met 0.5, Not Met 0). Seventeen criteria moved up on the evidence in their RTM rows.
Two were held back or moved the other way on purpose:

- **FR-015 stays Partially Met.** The reopen path and who may reject are a proposal (`DEC-019`), and the full
  permitted/forbidden transition matrix is not tested exhaustively.
- **NFR-004 drops to Partially Met.** The role matrix was not extended to the new operations.

Also still Partially Met: FR-002 (public registration conflicts with AC-002 and no change request exists), FR-012
(the requirement names priority, which has no field), NFR-001 (no cold-start measurement), NFR-003, NFR-008,
NFR-011 and NFR-014. Not Met: NFR-002, NFR-010, NFR-013.

The score sits close to the 80% target. Judgement calls an assessor could reasonably make differently: FR-004 and
FR-009 (email verified only against a local sink), FR-021 (provisional targets, exactly-T not tested) and
FR-025/NFR-006 (the audit triggers do not protect against direct access to the database file).

## Limits

No hosted run, no cold-start or capacity measurement, no external email delivery, no human usability retest, and no
independent security review. CI results for the release commit are on GitHub.
