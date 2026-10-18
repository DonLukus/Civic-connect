# DEC-008 recommendation: stack, architecture and deployment platform

**Status: PROPOSED for team review. Not approved.** DEC-008 stays `Deferred` in `decision-log.csv` and
ADR-001/ADR-007 stay `Proposed` until Don, Masego and Emile record agreement. Nothing here changes a
baselined identifier. Prepared 2026-10-17 by Don (AI-assisted, see PR declaration).

## 1. What the evidence already shows

| Fact | Source |
|---|---|
| The implementation is Python 3.11+ / Flask 3.1.3, server-rendered, one deployable unit, SQLite, bcrypt. Node.js was only ever a scored alternative (29/40 vs 37/40 for Flask, ADR-001). | `requirements.txt`, ADR-001 |
| 60 tests pass on `main` (6e99ae6); line coverage 83% overall, 91% in `request_service.py`. | local run 2026-10-17 |
| NFR-001 scenario (500 records, 10 distinct Staff users, 300 s, warm) gave 8,503/8,503 OK, p95 0.422 s. Local Waitress, not a hosted instance. | `docs/release/m3-release-evidence-summary.md` |
| Render free-tier local disk lost request #1 after a redeploy (M2). Cause was never confirmed on the original service. | DEC-008 evidence, `poc-log.md` |
| Local restart preserves SQLite; this does not show hosted redeploy persistence. | `docs/deployment/m3-staging.md` |

## 2. Architecture Significant Requirements (consolidated)

| ASR | Requirement | Measurable target | Architectural consequence | Current evidence |
|---|---|---|---|---|
| Performance | NFR-001 | p95 <= 2.0 s, 500 records, 10 users, 5 min, warm | Indexed filtered query; no per-request heavy work | Local pass (0.422 s); hosted run missing |
| Availability | NFR-002 | >= 95% 07:00-18:00 SAST weekdays; cold start <= 30 s accepted | Single unit; host that sleeps is tolerated, one that loses data is not | None |
| Security | NFR-003, 004, 005, 012, 014 | bcrypt >= 10; 0 unauthorised successes; 0 secrets in history | Authorisation in the service layer, not per screen (ADR-007); secrets only in host env | Matrix tests, bcrypt check; history scan not archived |
| Cost | NFR-010, CN-03 | R0.00 recurring | Rules out paid tiers and extra services | No cost review |
| Auditability | NFR-006 | 100% of changes logged; no app path edits the log | Audit write in the same transaction as the change; transactional store | Tests pass |
| Recoverability | NFR-011 | Daily backup, RPO 24 h, RTO 4 h, one verified restore | Store must support online backup and be durable | One manual SQLite drill |
| Capacity | NFR-013 | 500 users, 5,000 requests inside free-tier storage, NFR-001 still met | Storage ceiling is a host property | None |

## 3. Weighted decision matrix

Scores 1-5 (5 best), weights sum to 100. Scores are the author's judgement from the evidence above and
are open to challenge in review. Total = sum(weight x score) / 5.

| Criterion | Weight |
|---|---|
| Compatibility with Belgium Campus machines | 15 |
| Team experience | 20 |
| R0 cost | 20 |
| Testing | 10 |
| Maintainability | 10 |
| Hosting fit and durability | 25 |

### 3.1 Language / framework

| Option | BC | Team | R0 | Test | Maint | Host | Total |
|---|---|---|---|---|---|---|---|
| **A. Flask (continue)** | 4 | 4 | 5 | 5 | 4 | 4 | **86** |
| B. Node/Express | 4 | 3 | 5 | 3 | 4 | 4 | 78 |
| C. Django | 4 | 2 | 5 | 4 | 4 | 4 | 76 |

A leads because it continues tested code (B or C would rebuild 60 tests and the audited slice) and BC
install is verified (Python 3.14.5, 2026-10-05). Gunicorn does not run on Windows; Waitress does
(`requirements-staging.txt`).

### 3.2 Data store and deployment platform

| Option | BC | Team | R0 | Test | Maint | Host | Total |
|---|---|---|---|---|---|---|---|
| H1. Free host + SQLite on its local disk | 5 | 5 | 5 | 4 | 3 | 1 | 74 |
| H2. Free host + external free-tier PostgreSQL | 4 | 3 | 5 | 4 | 4 | 3 | 75 |
| H3. Simulated production on a BC machine (Waitress, local DB) | 5 | 4 | 5 | 4 | 3 | 2 | 75 |
| H4. Paid host with persistent disk/DB | 4 | 4 | 1 | 4 | 4 | 5 | 73 |

**Reading this table honestly:** the spread is 2 points, which is within scoring error. The matrix does
not choose a platform; only the persistence experiment in section 5 can. H4 is excluded outright because
NFR-010 is a Must at R0.00. H1's host score is 1 because the only hosted result we have is data loss.

## 4. Recommendation

1. **Stack and architecture: adopt A.** Single deployable Flask unit, server-rendered pages, authorisation
   and audit in the service layer. This is decisive (86 vs 78).
2. **Database: SQLite for development and test; PostgreSQL for any hosted environment**, because the
   hosted failure to date is storage durability and online backup/restore (NFR-011) is first-class in
   PostgreSQL. This needs an adapter and migration work in `src/persistence` that does not exist yet
   (queries and `BEGIN IMMEDIATE` are SQLite-specific). Effort is not yet estimated.
3. **Identity: keep in-app bcrypt accounts (ADR-007)**, public registration limited to Requester. A
   hosted identity provider adds a service and a dependency for no stated requirement. Trade-off: we own
   password reset, rate limiting and email verification, none of which exist yet.
4. **Hosting: undecided.** Run the section 5 experiment on H2, with H3 as the fallback. Do not name a
   provider until its current free-tier limits are read from its own documentation and recorded with a date;
   I have not verified any provider's current terms.
5. **Release posture: staging with an evidence-based no-go for public production** until durable hosted
   storage, external email and the NFR-002/011/013 evidence exist. This matches the current release summary.

## 5. Evidence still required before approval

- Provider free-tier limits (storage, expiry, backups, sleep behaviour), quoted with source and date.
- Persistence proof: write a record, redeploy, restart and idle-sleep the service, then read it back; three
  repeats, results logged.
- Hosted NFR-001 run using the existing load script; cold-start time recorded separately.
- Confirmation that the chosen database driver installs on a BC machine.
- A decision from the team on legacy password hashes and outbox recovery (carried from the release summary).

## 6. Trade-offs accepted if the recommendation is approved

- One process is a larger blast radius than separate services (ADR-001 security score 3 vs 4), accepted for cost.
- PostgreSQL costs migration effort and a second moving part versus SQLite's zero-setup.
- Free tiers may sleep or expire; NFR-002 already accepts cold starts, not data loss.
- Keeping our own auth means owning its hardening.

## 7. Decisions requested

1. Approve A as the stack and architecture (supersedes the `Proposed` status of ADR-001 once recorded there).
2. Approve PostgreSQL-for-hosted as the direction, conditional on section 5.
3. Agree the hosting selection method (experiment first), and that H4 is out.

Approvals are to be recorded in the PR reviews and then in `decision-log.csv`, not by this file.
